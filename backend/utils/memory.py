# backend/utils/memory.py
import os, json, re
from typing import Dict, List

DATA_DIR = "backend/data"
CHAR_PATH = os.path.join(DATA_DIR, "characters.json")

class CharacterMemory:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(CHAR_PATH):
            with open(CHAR_PATH, "w", encoding="utf-8") as f:
                json.dump({}, f)
        with open(CHAR_PATH, "r", encoding="utf-8") as f:
            self.db: Dict[str, Dict] = json.load(f)

    def save(self):
        with open(CHAR_PATH, "w", encoding="utf-8") as f:
            json.dump(self.db, f, ensure_ascii=False, indent=2)

    def bootstrap_from_beats(self, beats: List[Dict]):
        for b in beats:
            for name in set(re.findall(r"\b[A-Z][a-zA-Z']+\b", b.get("text", ""))):
                self.db.setdefault(name, {"traits": [], "first_seen": b.get("text", "")[:140]})
        self.save()

    def reinforce(self, name: str, trait: str):
        self.db.setdefault(name, {"traits": []})
        if trait not in self.db[name]["traits"]:
            self.db[name]["traits"].append(trait)
        self.save()

    def inject_consistency(self, text: str) -> str:
        if not self.db:
            return text
        hints = []
        for n, info in list(self.db.items())[:5]:
            if info.get("traits"):
                hints.append(f"{n}: {', '.join(info['traits'])}")
        if hints:
            return text + "\nCharacter continuity: " + "; ".join(hints)
        return text
