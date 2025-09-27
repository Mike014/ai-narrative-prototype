# engine/relay.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import os, requests
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).with_name(".env.relay"))

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

GROQ_KEY = os.environ.get("GROQ_API_KEY")
HF_KEY   = os.environ.get("HUGGINGFACE_API_KEY")

@app.get("/")
def root():
    return {"ok": True, "service": "dialoghi-relay"}

@app.post("/groq/chat")
async def groq_chat(req: Request):
    if not GROQ_KEY:
        raise HTTPException(500, "GROQ key missing on server")
    payload = await req.json()
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_KEY}"},
        json=payload, timeout=20
    )
    r.raise_for_status()
    return r.json()

@app.post("/hf/chat")
async def hf_chat(req: Request):
    if not HF_KEY:
        raise HTTPException(500, "HF key missing on server")
    payload = await req.json()
    r = requests.post(
        "https://api-inference.huggingface.co/models/<MODEL_ID>",
        headers={"Authorization": f"Bearer {HF_KEY}"},
        json=payload, timeout=20
    )
    r.raise_for_status()
    return r.json()
