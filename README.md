# SIVA - Minimal Patient Intake Voice Agent

This project is a minimal, from-scratch patient intake voice agent inspired by [Pipecat's patient-intake repo](https://github.com/pipecat-ai/pipecat/tree/main/examples/patient-intake).

## Quick Start

### Prerequisites
- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager

### Setup Instructions

1. **Clone the repository and navigate to the project root:**
   ```bash
   cd /path/to/leaping
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   uv pip install -r siva/requirements.txt
   ```

4. **Set up environment variables (optional):**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

5. **Run the server:**
   ```bash
   uvicorn siva.main:app --reload
   ```

The server will start at `http://127.0.0.1:8000`

### API Testing with curl

#### 1. Check if the server is running:
```bash
curl http://127.0.0.1:8000/
```

#### 2. Test the intake state machine:

**Start a new session (intro step):**
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-session-1", "message": ""}'
```

**Verify birthday (provide correct birthday):**
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-session-1", "message": "My birthday is 1983-01-01"}'
```

**List prescriptions:**
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-session-1", "message": "I take Lisinopril 10mg daily and Metformin 500mg twice daily"}'
```

**List symptoms:**
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-session-1", "message": "I have been experiencing headaches and fatigue"}'
```

**List allergies:**
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-session-1", "message": "I am allergic to penicillin"}'
```

#### 3. Test with wrong birthday (should prompt again):
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-session-2", "message": ""}'

curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-session-2", "message": "My birthday is 1990-05-15"}'
```

#### 4. Test multiple sessions:
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "another-session", "message": ""}'
```

### State Machine Flow

The intake process follows these steps:
1. **intro** → Introduction and birthday request
2. **verify_birthday** → Verify identity (expects "1983-01-01")
3. **list_prescriptions** → Collect current medications
4. **list_symptoms** → Collect current symptoms
5. **list_allergies** → Collect known allergies
6. **completed** → Intake process finished

---

## Pipecat-AI Utility Overview (for future reimplementation)

The original codebase used `pipecat-ai` to provide the following features:

- **Voice Activity Detection (VAD):**
  - `SileroVADAnalyzer` for detecting speech in audio streams.
- **Audio Frame Handling:**
  - `OutputAudioRawFrame` for managing raw audio data.
- **Pipeline Architecture:**
  - `Pipeline`, `PipelineRunner`, `PipelineTask`, `PipelineParams` for chaining together audio, LLM, and TTS processing steps.
- **LLM Integration:**
  - `OpenAILLMService`, `OpenAILLMContext`, `OpenAILLMContextFrame` for managing conversation state and interacting with OpenAI LLMs.
  - Function call registration and context management for conversational flows.
- **Text-to-Speech (TTS):**
  - `CartesiaTTSService` for generating speech from text using Cartesia.
- **Audio/Video Transport:**
  - `DailyTransport`, `DailyParams` for connecting to Daily.co rooms and handling real-time audio/video.
  - `DailyRESTHelper`, `DailyRoomParams` for room management and token generation.
- **Frame Logging:**
  - `FrameLogger` for debugging and logging pipeline frames.
- **General Pipeline Processing:**
  - `FrameDirection`, `FrameProcessor` for managing the flow of data through the pipeline.

---

## Next Steps

- Remove all `pipecat-ai` dependencies from the codebase.
- Start with a minimal FastAPI server and add features incrementally.
