# main.py
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from typing import Literal
import os
import httpx # For making asynchronous HTTP requests

# Initialize FastAPI app
app = FastAPI(
    title="AI Homework Helper Backend",
    description="FastAPI backend for processing homework requests with Gemini and Llama AI.",
    version="1.0.0"
)

# --- CORS Configuration ---
# This is crucial for allowing your Vercel frontend to communicate with this backend.
# I have updated the 'origins' list with your Vercel frontend URL: https://note-book-ai-v2.vercel.app/
origins = [
    "http://localhost:3000",  # For local Next.js development
    "https://note-book-ai-v2.vercel.app", # Your actual Vercel frontend URL
]


# --- Hardcoded User for Login ---
# These values will be loaded from environment variables on Railway.
HARDCODED_USERNAME = os.getenv("APP_USERNAME", "user")
HARDCODED_PASSWORD = os.getenv("APP_PASSWORD", "password123")

# --- Pydantic Models for Request/Response Bodies ---

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    message: str
    status: str

class HomeworkRequest(BaseModel):
    study_content: str
    prompt: str
    api_choice: Literal["gemini", "llama"] # Ensures only 'gemini' or 'llama' are accepted

class HomeworkResponse(BaseModel):
    # Resolve Pydantic UserWarning: Field "model_used" has conflict with protected namespace "model_".
    model_config = ConfigDict(protected_namespaces=())

    output: str
    model_used: str

# --- API Keys (Environment Variables) ---
# IMPORTANT: These are loaded from environment variables.
# You will need to set these on Railway.com and in your local .env file.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # Loaded from environment variable
LLAMA_API_KEY = os.getenv("LLAMA_API_KEY") # Loaded from environment variable

# --- Routes ---

@app.get("/")
async def read_root():
    """Root endpoint to check if the API is running."""
    return {"message": "AI Homework Helper Backend is running!"}

@app.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Handles user login with hardcoded credentials.
    """
    if request.username == HARDCODED_USERNAME and request.password == HARDCODED_PASSWORD:
        return {"message": "Login successful!", "status": "success"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.post("/process_homework", response_model=HomeworkResponse)
async def process_homework(request: HomeworkRequest):
    """
    Processes homework requests using either Gemini or Llama AI based on user choice.
    """
    ai_output = ""
    model_used = request.api_choice

    if request.api_choice == "gemini":
        if not GEMINI_API_KEY:
            raise HTTPException(status_code=500, detail="Gemini API Key not configured on the server.")
        try:
            full_prompt = f"Study Content: {request.study_content}\n\nUser Prompt: {request.prompt}"
            
            gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
            
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": full_prompt}
                        ]
                    }
                ]
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(gemini_api_url, json=payload, timeout=60.0)
                response.raise_for_status()
                result = response.json()

            if result and result.get("candidates") and result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts"):
                ai_output = result["candidates"][0]["content"]["parts"][0]["text"]
            else:
                ai_output = "Error: Could not get a valid response from Gemini AI."
                print(f"Gemini API raw response: {result}")

        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Gemini API request failed: {e}. Check network or API key.")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Gemini API returned an error: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred with Gemini API: {e}")

    elif request.api_choice == "llama":
        if not LLAMA_API_KEY:
            raise HTTPException(status_code=500, detail="Llama API Key not configured on the server.")
        try:
            # --- ACTUAL GROQ CLOUD (LLAMA) API INTEGRATION ---
            groq_api_url = "https://api.groq.com/openai/v1/chat/completions"
            
            # Combine study content and prompt for the Llama model
            full_llama_prompt = f"Study Content: {request.study_content}\n\nUser Prompt: {request.prompt}"

            llama_payload = {
                "model": "llama3-8b-8192", # Using a common Llama-3 model from Groq
                "messages": [{"role": "user", "content": full_llama_prompt}],
                "max_tokens": 1024, # You can adjust this as needed
                "temperature": 0.7, # You can adjust this as needed
            }
            
            async with httpx.AsyncClient() as client:
                llama_response = await client.post(
                    groq_api_url,
                    json=llama_payload,
                    headers={
                        "Authorization": f"Bearer {LLAMA_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    timeout=60.0 # Added timeout
                )
                llama_response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
                llama_result = llama_response.json()

            if llama_result and llama_result.get("choices") and llama_result["choices"][0].get("message") and llama_result["choices"][0]["message"].get("content"):
                ai_output = llama_result["choices"][0]["message"]["content"]
            else:
                ai_output = "Error: Could not get a valid response from Llama AI (Groq)."
                print(f"Llama API raw response: {llama_result}") # Log raw response for debugging

        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Llama API request failed: {e}. Check network or API key.")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Llama API returned an error: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred with Llama API: {e}")

    return {"output": ai_output, "model_used": model_used}