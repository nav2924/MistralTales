from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from utils.text_gen import ask_clarifiers, improve_prompt

router = APIRouter()

class PromptIn(BaseModel):
    seed_prompt: str

@router.post("/clarify")
def clarify(p: PromptIn):
    return {"questions": ask_clarifiers(p.seed_prompt)}

class Answers(BaseModel):
    seed_prompt: str
    answers: List[str]

@router.post("/upgrade")
def upgrade(a: Answers):
    return {"prompt": improve_prompt(a.seed_prompt, a.answers)}
