# backend/utils/orchestrator.py
import os
from typing import List, Dict
from utils.image_generator import generate_image

STYLE_HINT = "illustration, cinematic composition, SDXL quality, vivid lighting, storybook"

def _scene_prompt(beat: Dict) -> str:
    base = beat.get("text", "")
    return f"{base}\n\nIllustration style: {STYLE_HINT}"

def render_scenes(session_id: str, beats: List[Dict]) -> List[str]:
    paths: List[str] = []
    for i, beat in enumerate(beats, start=1):
        prompt = _scene_prompt(beat)
        filename = f"{session_id}_scene_{i}.png"
        path = generate_image(prompt=prompt, output_name=filename)
        paths.append(path)  # absolute filesystem paths; frontend uses basename to build /outputs URLs
    return paths
