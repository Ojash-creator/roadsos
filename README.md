# RoadSoS 🚨 (Ollama Edition — 100% Free, No API Key)
**Emergency Services Chatbot — Road Safety Hackathon 2026, IIT Madras**

## Setup (One Time)

### Step 1 — Install Ollama
Download from https://ollama.com/download and install it.

### Step 2 — Pull a free AI model
```bash
ollama pull llama3
```
> Other options: `ollama pull mistral` or `ollama pull gemma2`

### Step 3 — Install Python dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Initialize the database
```bash
python database.py
```

### Step 5 — Run the chatbot
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Step 6 — Open browser
```
http://localhost:8000
```

## No API key needed. No internet needed. Completely free.

## Change the AI model (optional)
```bash
# Use a different model
export OLLAMA_MODEL=mistral
uvicorn main:app --port 8000
```

## File Structure
```
roadsos/
├── main.py          # FastAPI + Ollama chatbot
├── database.py      # SQLite DB with 44+ emergency services
├── offline.py       # Fallback if Ollama not running
├── requirements.txt # fastapi, uvicorn, ollama, pydantic
└── static/
    └── index.html   # Web chat UI
```
