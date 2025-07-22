from pydantic import BaseModel

class HomeworkRequest(BaseModel):
    studyText: str
    promptText: str
    model: str
