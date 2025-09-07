
# 📖 MistralTales

MistralTales is an AI-powered interactive storytelling platform built with FastAPI (backend) and Streamlit (frontend).
It lets users generate branching stories, create AI-generated illustrations, and export their adventures into PDFs or narrated videos.

## Folder Structure(After setting up)

```
├── 📁 .git/ 🚫 (auto-hidden)
├── 📁 Docs/ 🚫 (auto-hidden)
├── 📁 backend/
│   ├── 📁 __pycache__/ 🚫 (auto-hidden)
│   ├── 📁 backend/
│   │   └── 📁 data/
│   │       └── 📄 characters.json 🚫 (auto-hidden)
│   ├── 📁 data/
│   │   ├── 📁 sessions/ 🚫 (auto-hidden)
│   │   └── 📄 characters.json 🚫 (auto-hidden)
│   ├── 📁 outputs/ 🚫 (auto-hidden)
│   ├── 📁 routers/
│   │   ├── 📁 __pycache__/ 🚫 (auto-hidden)
│   │   ├── 🐍 __init__.py
│   │   ├── 🐍 co_creator.py
│   │   ├── 🐍 export.py
│   │   └── 🐍 story.py
│   ├── 📁 utils/
│   │   ├── 📁 __pycache__/ 🚫 (auto-hidden)
│   │   ├── 🐍 __init__.py
│   │   ├── 🐍 image_generator.py
│   │   ├── 🐍 memory.py
│   │   ├── 🐍 orchestrator.py
│   │   └── 🐍 text_gen.py
│   ├── 📁 venv/ 🚫 (auto-hidden)
│   ├── 🔒 .env 🚫 (auto-hidden)
│   ├── 🐍 main.py
│   └── 📄 requirments.txt
├── 📁 frontend/
│   ├── 📁 venv/ 🚫 (auto-hidden)
│   ├── 🐍 app.py
│   ├── 🐍 branching.py
│   └── 📄 requirments.txt
├── 📁 outputs/ 🚫 (auto-hidden)
├── 🚫 .gitignore
└── 📖 README.md
```

## ✨Features

- 📝 Interactive story generation with branching choices
- 🎨 AI-generated illustrations (Stable Diffusion XL)
- 📄 Export as PDF
- 🎬 Export as narrated video (gTTS + MoviePy)
- ⚡ Backend with FastAPI
- 🖥️ Frontend with Streamlit
- 📂 Session-based story memory
- 🌍 Multi-audience genres: Kids, Teens, Adults

## 🛠 Tech

- Backend: FastAPI, HuggingFace Hub, fpdf2, gTTS, MoviePy
- Frontend: Streamlit
- AI Models: Mistral (via Ollama), Stable Diffusion XL (HuggingFace)
- Other: Python-dotenv, Requests, Pillow

## ⚙️ Installation
```bash
git clone https://github.com/nav2924/MistralTales.git
cd MistralTales
```
## ▶️ Run Locally

Backend
```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows
pip install -r requirments.txt
uvicorn main:app --reload
```
Once successfully installed backend will run on 
```
http://localhost:8000
```

Frontend
```bash
cd frontend
pip install -r requirments.txt
streamlit run branching.py
```
Once successfully installed frontend will run on 
```
http://localhost:8501
 ```

## 📚 Usage/Examples
```python
Prompt: "A lonely robot finds a flower in a post-apocalyptic city."
Genre: Sci-fi
Tone: Light
Audience: Teens
Scenes: 4
```
- Generates branching story with AI images. 
- Export as PDF/Video.

## 📡 API Reference
Start Story
```
POST /story/start
```

Branch
```
POST /story/branch
```

Render Images
```
POST /story/render
```

Export PDF
```
POST /export/pdf
```
Export Video
```
POST /export/video
```

## 🔑 Environment Variables
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=mistral
HF_TOKEN=your_huggingface_token

## 🚀 Deployment
- Backend: Deploy with Docker, Heroku, or Railway
- Frontend: Deploy Streamlit on Streamlit Cloud

## 🧪 Running Tests
```
pytest tests/
```

## 🔧 Optimizations
- Async support for image generation
- Queueing system for batch requests
- GPU-accelerated inference


## 🛣 Roadmap
 - Add multiplayer co-creation mode
 - Export EPUB format
 - Add character avatars
 - Voice cloning for narration

## 📘 Lessons
- Handling Unicode text in PDFs (smart quotes, dashes)
- Streamlit UI state management with session_state
- Dealing with moviepy import quirks

## ❓ FAQ
Q: Images not loading in frontend?

A: Make sure backend app.mount("/outputs", StaticFiles(...)) is set correctly.

Q: Video export fails?

A: Install ffmpeg and ensure it's in PATH.

## 🙏 Acknowledgements
- HuggingFace for SDXL
- Ollama/Mistral
- Streamlit team
- MoviePy & gTTS maintainers

## Demo
<img width="1919" height="876" alt="image" src="https://github.com/user-attachments/assets/ae88bb8e-0b93-4d1c-977e-6963a2c42e1a" />

