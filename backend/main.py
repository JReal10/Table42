from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from tests.test_routes import router as test_router

app = FastAPI(title = "ARQ API")

# Include test routes under a prefix (optional)
#app.include_router(test_router,prefix = "api")

class QueryRequest(BaseModel):
  query: str
  
class QueryResponse(BaseModel):
  responses:str

@app.get("/")
async def test():
  return ("testing")


def start_server():
  uvicorn.run(app, host = "localhost", port = 8000)
  
if __name__ == "__main__":
  start_server()