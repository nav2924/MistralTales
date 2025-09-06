# backend/main.py

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import requests
from dotenv import load_dotenv
import os

from utils.image_generator import generate_image
from fastapi.staticfiles import StaticFiles

# Initialize FastAPI app
app = FastAPI()

# Serve static image files from the outputs directory
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# Load environment variables
load_dotenv()
OLLAMA_URL = os.getenv("OLLAMA_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

# Input and Output Models
class StoryInput(BaseModel):
    prompt: str
    genre: str = "Fantasy"
    tone: str = "Lighthearted"
    audience: str = "Kids"

class Scene(BaseModel):
    text: str
    image_path: str = None

class StoryOutput(BaseModel):
    scenes: List[Scene]

# Story generation with Mistral via Ollama
def call_mistral(prompt: str) -> str:
    response = requests.post(OLLAMA_URL, json={
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    })
    return response.json()["response"]

# Story prompt builder
def build_story_prompt(input: StoryInput) -> str:
    return (
        f"You are a children's story writer. Write a story in 4 parts:\n"
        f"1. Introduction\n2. Rising Action\n3. Climax\n4. Resolution\n\n"
        f"Make it {input.tone.lower()} in tone and suitable for {input.audience.lower()}.\n"
        f"Genre: {input.genre}\n\n"
        f"Story idea: {input.prompt}"
    )

# API Route
@app.post("/generate_story", response_model=StoryOutput)
def generate_story(input: StoryInput):
    prompt = build_story_prompt(input)
    story = call_mistral(prompt)

    raw_parts = story.split("\n\n")
    scenes = []
    scene_index = 1

    for part in raw_parts:
        text = part.strip()
        if not text or text.lower().startswith(("1.", "2.", "3.", "4.", "title", "introduction", "rising action", "climax", "resolution")):
            continue

        image_filename = f"scene_{scene_index}.png"
        generate_image(prompt=text, output_name=image_filename)

        # Return image as public URL
        image_url = f"http://localhost:8000/outputs/{image_filename}"

        scenes.append(Scene(text=text, image_path=image_url))
        scene_index += 1

    return StoryOutput(scenes=scenes)

