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
    provider="nscale"
)

def generate_image(prompt: str, output_name: str = "output.png") -> str:
    image: Image.Image = client.text_to_image(
        prompt,
        guidance_scale=7,
        num_inference_steps=30,
    )

    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, output_name)

    image.save(path)
    return path
