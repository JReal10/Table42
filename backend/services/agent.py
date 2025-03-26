# agent.py
from ai_agent_component import asr
from ai_agent_component import tts
from ai_agent_component import rag
from ai_agent_component import conversationalAI_agent

def main():
    # Step 1: Automatic Speech Recognition (ASR)
    asr_client = asr.SilenceDetectingASRService
    print("Listening for user input...")
    asr_service = asr_client(
        silence_threshold=1000,  # Energy threshold for silence detection
        silence_duration=3.2     # Duration of silence to end recording (seconds)
    )
    
    print("Please speak now...")
    # Use the transcribe method to record and get the transcription as text.
    transcribed_text = asr_service.transcribe()
    print("Transcribed text:", transcribed_text)

    # Step 2: Retrieval-Augmented Generation (RAG) - optional context enrichment
    rag_client = rag.RAGSystem(index_name = "conv-ai")
    enriched_context = rag_client.similarity_search_with_score(transcribed_text, k = 1)
    
    print("Context: ", enriched_context)
    
    agent_response = conversationalAI_agent.handle_transcribed_input(transcribed_text, enriched_context)
    
    print (agent_response)
    
    # Step 4: Text-to-Speech (TTS)
    tts.text_to_speech(agent_response)


if __name__ == '__main__':
    main()