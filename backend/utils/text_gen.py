# backend/utils/text_gen.py
import os, requests, json
from typing import List, Dict, Optional

OLLAMA_URL = os.getenv("OLLAMA_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

SYSTEM_BEATS = (
    "You are a story outliner. Given a premise, produce N numbered scene beats.\n"
    "Each beat: 2-4 sentences + 2-3 concise choices that branch the story.\n"
    "Return JSON list: [{\"text\": \"...\", \"choices\": [\"...\",\"...\"]}]."
).strip()

SYSTEM_BRANCH = (
    "Extend an existing story. Given prior beats and a chosen branch at step K,\n"
    "continue with coherent beats that follow the selected choice.\n"
    "Return the full updated list of beats in the same JSON format."
).strip()

SYSTEM_CLARIFIERS = (
    "Ask 3-5 short clarifying questions to improve a story prompt: genre, tone, characters, "
    "setting, constraints.\nReturn JSON list of strings."
).strip()

SYSTEM_UPGRADE = (
    "Given a seed prompt and answers to clarifiers, produce one improved prompt (<120 words)."
).strip()


def _ollama(prompt: str) -> str:
    r = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=120,
    )
    r.raise_for_status()
    return r.json().get("response", "")


def generate_beats(
    prompt: str,
    genre: Optional[str],
    tone: Optional[str],
    audience: Optional[str],
    scenes: int,
    guidance: Optional[str],
) -> List[Dict]:
    user = (
        f"{SYSTEM_BEATS}\n\n"
        f"Prompt: {prompt}\nGenre: {genre}\nTone: {tone}\nAudience: {audience}\nScenes: {scenes}\nGuidance: {guidance}"
    )
    text = _ollama(user)
    try:
        data = json.loads(text)
        assert isinstance(data, list)
        return data
    except Exception:
        return [{"text": text.strip(), "choices": ["Continue", "Twist"]}]


def continue_branch(base_beats: List[Dict], from_step: int, choice_idx: int) -> List[Dict]:
    user = (
        f"{SYSTEM_BRANCH}\n\n"
        f"Base beats: {json.dumps(base_beats, ensure_ascii=False)}\n"
        f"Branch from step: {from_step} pick choice index: {choice_idx}"
    )
    text = _ollama(user)
    try:
        data = json.loads(text)
        assert isinstance(data, list)
        return data
    except Exception:
        return base_beats


def ask_clarifiers(seed_prompt: str) -> List[str]:
    text = _ollama(f"{SYSTEM_CLARIFIERS}\n\nSeed: {seed_prompt}")
    try:
        data = json.loads(text)
        assert isinstance(data, list)
        return data
    except Exception:
        return ["What genre?", "Tone?", "Main character?", "Setting?", "Any constraints?"]


def improve_prompt(seed_prompt: str, answers: List[str]) -> str:
    joined = " | ".join(answers)
    return _ollama(f"{SYSTEM_UPGRADE}\n\nSeed: {seed_prompt}\nAnswers: {joined}")
