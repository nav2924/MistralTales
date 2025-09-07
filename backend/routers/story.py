from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import os, json, uuid

from utils.text_gen import generate_beats, continue_branch
from utils.orchestrator import render_scenes
from utils.memory import CharacterMemory

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(HERE), "data")
SESSIONS_DIR = os.path.join(DATA_DIR, "sessions")

router = APIRouter()

class StoryInit(BaseModel):
    prompt: str
    genre: Optional[str] = None
    tone: Optional[str] = None
    audience: Optional[str] = None
    scenes: int = Field(default=4, ge=2, le=8)
    guidance: Optional[str] = None

class StoryBranch(BaseModel):
    session_id: str
    choice_idx: int
    step: int

@router.post("/start")
def start_story(payload: StoryInit):
    os.makedirs(SESSIONS_DIR, exist_ok=True)

    beats = generate_beats(
        prompt=payload.prompt,
        genre=payload.genre,
        tone=payload.tone,
        audience=payload.audience,
        scenes=payload.scenes,
        guidance=payload.guidance,
    )

    mem = CharacterMemory()
    mem.bootstrap_from_beats(beats)

    session_id = str(uuid.uuid4())
    session = {
        "session_id": session_id,
        "config": payload.model_dump(),
        "beats": beats,
        "images": [],
        "current": 0,
    }

    with open(os.path.join(SESSIONS_DIR, f"{session_id}.json"), "w", encoding="utf-8") as f:
        json.dump(session, f, ensure_ascii=False, indent=2)

    return {"session_id": session_id, "beats": beats}

@router.post("/branch")
def branch_story(payload: StoryBranch):
    path = os.path.join(SESSIONS_DIR, f"{payload.session_id}.json")
    if not os.path.exists(path):
        raise HTTPException(404, "session not found")

    with open(path, "r", encoding="utf-8") as f:
        session = json.load(f)

    beats = continue_branch(
        base_beats=session["beats"],
        from_step=payload.step,
        choice_idx=payload.choice_idx,
    )
    session["beats"] = beats

    with open(path, "w", encoding="utf-8") as f:
        json.dump(session, f, ensure_ascii=False, indent=2)

    return {"session_id": payload.session_id, "beats": beats}

@router.post("/render")
def render_session(session_id: str):
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if not os.path.exists(path):
        raise HTTPException(404, "session not found")

    with open(path, "r", encoding="utf-8") as f:
        session = json.load(f)

    images = render_scenes(session_id=session_id, beats=session["beats"])
    session["images"] = images

    with open(path, "w", encoding="utf-8") as f:
        json.dump(session, f, ensure_ascii=False, indent=2)

    return {"session_id": session_id, "images": images}

@router.get("/session/{session_id}")
def get_session(session_id: str):
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if not os.path.exists(path):
        raise HTTPException(404, "session not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
