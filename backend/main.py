# backend/main.py
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import requests
from dotenv import load_dotenv
import os

from utils.image_generator import generate_image
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()
OLLAMA_URL = os.getenv("OLLAMA_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

if not OLLAMA_URL or not OLLAMA_MODEL:
    raise RuntimeError("Set OLLAMA_URL and OLLAMA_MODEL in .env")

# Paths
HERE = os.path.dirname(os.path.abspath(__file__))
# ✅ Serve and save under backend/outputs (matches where your generator writes)
OUTPUTS_DIR = os.path.join(HERE, "outputs")
DATA_DIR = os.path.join(HERE, "data")
SESSIONS_DIR = os.path.join(DATA_DIR, "sessions")
CHAR_PATH = os.path.join(DATA_DIR, "characters.json")

# Ensure required dirs
def _ensure_dirs():
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    if not os.path.exists(CHAR_PATH):
        import json
        with open(CHAR_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f)

# Initialize FastAPI app
app = FastAPI(title="StoryGen API (HF)", version="1.0.0")

# CORS (for Streamlit)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static image files from the outputs directory
_ensure_dirs()
app.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")

# -----------------------------
# Linear story generation models
# -----------------------------
class StoryInput(BaseModel):
    prompt: str
    genre: str = "Fantasy"
    tone: str = "Lighthearted"
    audience: str = "Kids"

class Scene(BaseModel):
    text: str
    image_path: Optional[str] = None  # Python 3.9 compatible

class StoryOutput(BaseModel):
    scenes: List[Scene]

# Story generation with Mistral via Ollama (existing)
def call_mistral(prompt: str) -> str:
    resp = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    if "response" not in data:
        raise HTTPException(502, "Ollama returned unexpected payload")
    return data["response"]

# Story prompt builder (existing)
def build_story_prompt(input: StoryInput) -> str:
    return (
        f"You are a children's story writer. Write a story in 4 parts:\n"
        f"1. Introduction\n2. Rising Action\n3. Climax\n4. Resolution\n\n"
        f"Make it {input.tone.lower()} in tone and suitable for {input.audience.lower()}.\n"
        f"Genre: {input.genre}\n\n"
        f"Story idea: {input.prompt}"
    )

# Helper for public URL
def _public_image_url(request: Request, filename: str) -> str:
    base = str(request.base_url).rstrip("/")
    return f"{base}/outputs/{filename}"

# API Route (existing linear)
@app.post("/generate_story", response_model=StoryOutput)
def generate_story(input: StoryInput, request: Request):
    prompt = build_story_prompt(input)
    story = call_mistral(prompt)

    raw_parts = story.split("\n\n")
    scenes: List[Scene] = []
    scene_index = 1

    for part in raw_parts:
        text = part.strip()
        # Skip headings/labels; keep actual paragraphs
        if not text or text.lower().startswith(
            ("1.", "2.", "3.", "4.", "title", "introduction", "rising action", "climax", "resolution")
        ):
            continue

        image_filename = f"scene_{scene_index}.png"
        generate_image(prompt=text, output_name=image_filename)
        scenes.append(Scene(text=text, image_path=_public_image_url(request, image_filename)))
        scene_index += 1

    return StoryOutput(scenes=scenes)

# -----------------------------------
# Feature routers (branching, co-creator, export)
# -----------------------------------
from routers.story import router as story_router
from routers.co_creator import router as coco_router  # type: ignore
from routers.export import router as export_router

app.include_router(story_router, prefix="/story", tags=["story"])
app.include_router(coco_router,  prefix="/co",    tags=["co-creator"])
app.include_router(export_router, prefix="/export", tags=["export"])

@app.get("/")
def root():
    return {"ok": True, "service": "StoryGen API (HF)"}
