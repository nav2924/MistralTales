# backend/utils/image_generator.py
import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
from PIL import Image

# Load variables from .env
load_dotenv()

# Load HF token from env
HF_TOKEN = os.getenv("HF_TOKEN")

client = InferenceClient(
    model="stabilityai/stable-diffusion-xl-base-1.0",
    token=HF_TOKEN,
    provider="nscale",
)

# ✅ Resolve to backend/outputs no matter where the process is started
HERE = os.path.dirname(os.path.abspath(__file__))         # .../backend/utils
OUTPUTS_DIR = os.path.normpath(os.path.join(HERE, "..", "outputs"))  # .../backend/outputs
os.makedirs(OUTPUTS_DIR, exist_ok=True)

def generate_image(prompt: str, output_name: str = "output.png") -> str:
    image: Image.Image = client.text_to_image(
        prompt,
        guidance_scale=7,
        num_inference_steps=30,
    )
    path = os.path.join(OUTPUTS_DIR, output_name)
    image.save(path)
    return path  # absolute filesystem path
