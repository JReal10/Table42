import os
from pydantic import BaseModel
import uvicorn
import websockets
import base64
import json
from fastapi import FastAPI, BackgroundTasks, Request, WebSocket
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.twiml.voice_response import VoiceResponse, Connect, Say, Stream
from twilio.rest import Client
from dotenv import load_dotenv
import asyncio

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
client = Client(account_sid, auth_token)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PORT = int(os.getenv('PORT', 5050))

system_message = (
  "You are a helpful and bubbly AI assistant who loves to chat"
)

Voice = 'alloy'

LOG_EVENT_TYPES = [
  'response.content.done', 'rate_limits.updated', 'response.done', 'input_audio_buffer.committed', 'input_audio_buffer.speech_stopped', 'input_audio_buffer.speech_started', 'session.created'
]

app = FastAPI(title = "ARQ API")

@app.get("/", response_class= JSONResponse)
async def read_main():
    return {"msg": "Hello World"}

@app.api_route("/incoming-call", methods =["GET", "POST"])
async def handle_incoming_call(request: Request):
    response = VoiceResponse()
    response.say("Please wait while we connect your call to the A.I. voice assistant")
    response.pause(length = 1)
    response.say("O.K. you can start talking")
    host = request.url.hostname
    connect = Connect()
    connect.stream(url = f'wss://{host}/media-stream')
    response.append(connect)

    return HTMLResponse(content = str(response), media_type = "application/xml")

@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    print("Client connected")
    await websocket.accept()
    
    async with websockets.connect(
      'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17',
      extra_headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "OpenAI-Beta": "realtime=v1"
      }
    ) as openai_ws:
      await send_session_update(openai_ws)
      stream_sid = None
      
      async def receive_from_twilio():
        nonlocal stream_sid
        try:
          async for message in websocket.iter_text():
            data = json.loads(message)
            if data['event'] == 'start':
              stream_sid = data['start']['streamSid']
              print(f"Incoming stream has started {stream_sid}")
            elif data['event'] == 'media' and openai_ws.open:
              audio_append = {
                "type": "input_audio_buffer.append",
                "audio": data['media']['payload']
              }  
              await openai_ws.send(json.dumps(audio_append))
        except WebSocketDisconnect:
          print("Client disconnected")
          if openai_ws.open:
            await openai_ws.close()  
        
      async def send_to_twilio():
        nonlocal stream_sid
        try:
          async for openai_message in openai_ws:
            response = json.loads(openai_message)
            if response['type'] in LOG_EVENT_TYPES:
              print(f"Received event: {response['type']}", response)
            if response['type'] == 'session.updated':
              print("Session updated succesfully: ", response)
            if response['type'] == 'response.audio.delta' and response.get('delta'):
              try:
                audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                audio_delta = {
                  "event": "media",
                  "streamSid": stream_sid,
                  "media": {
                    "payload": audio_payload
                  }
                }
                await websocket.send_json(audio_delta)
              except Exception as e:
                print(f"Error processing audio data: {e}")
        except Exception as e:
          print(f"Error in send_to_twilio: {e}")
            
      await asyncio.gather(receive_from_twilio(), send_to_twilio())
           
async def send_session_update(openai_ws):
  session_update = {
    "type": "session.update",
    "session":{
      "turn_detection":{"type":"server_vad"},
      "input_audio_format": "g711_ulaw",
      "output_audio_format": "g711_ulaw",
      "voice": Voice,
      "instructions": system_message,
      "modalities": ["text", "audio"],
      "temperature": 0.8
    }
  }
  
  print('Sending session update: ', json.dumps(session_update))
  await openai_ws.send(json.dumps(session_update))

def start_server():
  uvicorn.run(app, host = "0.0.0.0", port = PORT)
  
if __name__ == "__main__":
  start_server()

