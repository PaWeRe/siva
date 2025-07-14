# SIVA - Minimal Patient Intake Voice Agent

A minimal, from-scratch voice agent for patient intake, featuring a pure HTML/JavaScript frontend and FastAPI backend. Designed for fast, natural, voice-driven data collection before a doctor visit.

---

## Quick Start

- **Requirements:** Python 3.10+, [uv](https://docs.astral.sh/uv/) (for venv & package management), browser with mic access
- **Setup:**
  1. Create & activate venv:
     ```bash
     uv venv .venv && source .venv/bin/activate
     ```
  2. Install dependencies:
     ```bash
     uv pip install -r siva/requirements.txt
     ```
  3. Add `.env` in `siva/` or root:
     ```
     OPENAI_API_KEY=sk-...your-key...
     CARTESIA_API_KEY=...your-key...
     ```

---

## Running the Voice Agent

### Option 1: Unified Launcher (Recommended)
```bash
cd siva
python run_voice_app.py
```
- Starts both backend (FastAPI) and frontend (voice client server)
- Opens [http://localhost:3000/voice_client.html](http://localhost:3000/voice_client.html)

### Option 2: Run Servers Separately
```bash
# Terminal 1 - Backend
cd siva
uvicorn main:app --host localhost --port 8000 --reload

# Terminal 2 - Voice Client
cd siva
python serve_client.py
```

---

## Using the Voice Client
1. Open [http://localhost:3000/voice_client.html](http://localhost:3000/voice_client.html)
2. Click the call button or press spacebar to start
3. Wait for the agent to speak, then respond when prompted
4. The agent will guide you through: full name, birthday, prescriptions, allergies, conditions, and reason for visit
5. Conversation ends automatically when all info is collected

---

## Debugging
- Run `python debug_conversation.py` to test backend logic step-by-step (no voice required)
- Check browser console (F12) for frontend logs
- Check terminal for backend logs

---

## System Overview
- **Frontend:** Pure HTML/JavaScript (`voice_client.html`), served by `serve_client.py`
- **Backend:** FastAPI (`main.py`)
- **Launcher:** `run_voice_app.py` (starts both servers)
- **Audio assets:** `assets/` (UI feedback sounds)
- **Models used:**
  - **TTS:** Cartesia Sonic-2 (`model_id="sonic-2"`)
  - **LLM:** OpenAI GPT-3.5 Turbo 1106 (`model="gpt-3.5-turbo-1106"`)
  - **STT:** OpenAI Whisper v1 (`model="whisper-1"`)

---

## Lessons Learned (and still learning)
- **Gradio is not ideal for voice agent streaming:** Handling real-time audio, state, and streaming with Gradio is difficult; a custom HTML/JS frontend is much more flexible for voice agents.
- **Recursive state-based LLM calls:** Managing state and recursive LLM function calls in the backend helps guide the conversation and prevents hallucinations 
- **Latency is critical and challenging:** Achieving low-latency (sub-second, e.g. 800ms) is very hard. See [Pipecat's latency discussion](https://gist.github.com/kwindla/f755284ef2b14730e1075c2ac803edcf). My current setup is still far from this target.
- **Voice agent architecture & model orchestration:** All practical voice agents today use a TTS-LLM-STT pipeline (not voice-to-voice) because voice-to-voice models are not yet good enough for instruction following and context engineering (it appears...?). Orchestrating these three models (TTS, LLM, STT) is non-trivial, especially when using different providers for each.
- ...

---

## Project Structure
```
siva/
  main.py
  run_voice_app.py
  serve_client.py
  voice_client.html
  requirements.txt
  assets/
    clack-short-quiet.wav
    clack-short.wav
    clack.wav
    ding.wav
    ding2.wav
    ding3.wav
  debug_conversation.py
  old/
    gradio_frontend.py
```
