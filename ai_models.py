import os
from dotenv import load_dotenv
load_dotenv()

import requests

def call_gemini_api(prompt, content):
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "prompt": prompt,
        "content": content
    }

    # This is just an example endpoint — use your actual Gemini endpoint
    response = requests.post(GEMINI_API_KEY, json=data, headers=headers)
    
    return response.json().get("text", "Error: No response")
