from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

class Prompt(BaseModel):
    message: str

@app.post("/generate")
async def generate_response(prompt: Prompt):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt.message}]
    )
    return {"reply": response.choices[0].message.content}

# Create a new helath check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}