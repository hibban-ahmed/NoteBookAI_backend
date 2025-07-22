# main.py
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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
# Replace 'https://your-vercel-frontend-url.vercel.app' with your actual Vercel deployment URL.
# During development, you might use ["http://localhost:3000"]
origins = [
    "http://localhost:3000",  # For local Next.js development
    "https://your-vercel-frontend-url.vercel.app", # REPLACE WITH YOUR ACTUAL VERCEl URL
    "https://ai-homework-helper-frontend-example.vercel.app" # Example placeholder
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"], # Allows all headers
)

# --- Hardcoded User for Login ---
# In a real application, you would use a database and proper password hashing (e.g., bcrypt).
HARDCODED_USERNAME = os.getenv("APP_USERNAME", "user")
HARDCODED_PASSWORD = os.getenv("APP_PASSWORD", "password123") # Store securely in env vars!

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
    output: str
    model_used: str

# --- API Keys (Environment Variables) ---
# IMPORTANT: Never hardcode API keys directly in your code.
# Use environment variables for production deployments (e.g., on Railway.com).
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLAMA_API_KEY = os.getenv("LLAMA_API_KEY") # Placeholder for Llama API key

# --- Dependency for Authentication (Simple placeholder) ---
# For this hardcoded single user, we'll just check if a valid login has occurred.
# In a real app, this would involve JWT tokens or session management.
def verify_auth(username: str = Depends(lambda x: x)): # This is a simplified placeholder
    # In a real scenario, you'd check for a valid session token or JWT
    # For this simple hardcoded user, we'll assume successful login grants access.
    # The actual login check happens in the /login endpoint.
    pass

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
        # In a real app, you'd generate and return a JWT token here
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
            raise HTTPException(status_code=500, detail="Gemini API Key not configured.")
        try:
            # Construct the prompt for Gemini
            full_prompt = f"Study Content: {request.study_content}\n\nUser Prompt: {request.prompt}"
            
            # Gemini API Endpoint (using gemini-2.0-flash as specified)
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
                response = await client.post(gemini_api_url, json=payload, timeout=60.0) # Added timeout
                response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
                result = response.json()

            if result and result.get("candidates") and result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts"):
                ai_output = result["candidates"][0]["content"]["parts"][0]["text"]
            else:
                ai_output = "Error: Could not get a valid response from Gemini AI."
                print(f"Gemini API raw response: {result}") # Log raw response for debugging

        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Gemini API request failed: {e}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Gemini API returned an error: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred with Gemini API: {e}")

    elif request.api_choice == "llama":
        if not LLAMA_API_KEY:
            raise HTTPException(status_code=500, detail="Llama API Key not configured.")
        try:
            # Placeholder for Llama API call logic
            # You would replace this with actual Llama API integration (e.g., using a library or direct HTTP calls)
            # Example:
            # llama_api_url = "YOUR_LLAMA_API_ENDPOINT"
            # llama_payload = {
            #     "model": "llama-2-7b-chat", # Example Llama model
            #     "prompt": f"Based on '{request.study_content}', {request.prompt}",
            #     "max_tokens": 500
            # }
            # async with httpx.AsyncClient() as client:
            #     llama_response = await client.post(llama_api_url, json=llama_payload, headers={"Authorization": f"Bearer {LLAMA_API_KEY}"})
            #     llama_response.raise_for_status()
            #     llama_result = llama_response.json()
            #     ai_output = llama_result.get("choices")[0].get("text") # Adjust based on actual Llama API response structure

            ai_output = f"This is a simulated response from Llama AI for: '{request.prompt}' based on your content. (Llama API integration pending)"

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred with Llama API (simulated): {e}")

    return {"output": ai_output, "model_used": model_used}

# To run this locally:
# 1. Save this as main.py
# 2. Create a requirements.txt file with:
#    fastapi==0.111.0
#    uvicorn==0.30.1
#    pydantic==2.7.4
#    python-dotenv==1.0.1 (optional, for local .env file)
#    httpx==0.27.0
# 3. Install dependencies: pip install -r requirements.txt
# 4. Set environment variables (e.g., in a .env file if using python-dotenv, or directly in your terminal):
#    export APP_USERNAME="user"
#    export APP_PASSWORD="password123"
#    export GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
#    export LLAMA_API_KEY="YOUR_LLAMA_API_KEY_HERE"
# 5. Run: uvicorn main:app --reload --host 0.0.0.0 --port 8000