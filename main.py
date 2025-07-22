from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from schemas import HomeworkRequest
from ai_models import call_gemini_api, call_llama_api
from auth import authenticate

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or set specific frontend domain
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/helper")
def process_homework(request: HomeworkRequest, auth=Depends(authenticate)):
    if request.model == "gemini":
        return {"response": call_gemini_api(request.promptText, request.studyText)}
    else:
        return {"response": call_llama_api(request.promptText, request.studyText)}
