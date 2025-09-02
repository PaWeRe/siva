# SIVA - Self-Improving Voice Agent Framework

Self-improving voice agent framework that learns from expert feedback by extracting important concepts from conversations and validating predictions with a local vector db of similar cases (used for few-shot prompting and confidence assessment) + optionally public knowledge sources. SIVA leverages **Sierra's [tau2-bench](https://github.com/taubeta/tau2-bench)** architecture for agent simulation and evaluation.

![SIVA Demo - 10x Speed](assets/siva_demo_10x.gif)

## 🚀 Quick Start

**Requirements:** Python 3.8+, [uv](https://docs.astral.sh/uv/) package manager, browser with microphone access

1. **Setup Environment:**
   ```bash
   # Using uv (automatically handles virtual environment)
   uv run python --version
   ```

2. **Configure API Keys** (`.env` file):
   ```
   OPENAI_API_KEY=sk-your-key-here
   CARTESIA_API_KEY=your-cartesia-key-here
   DOMAIN_API_KEY=your-domain-specific-key-here  # For domain-specific evidence sources
   ```

3. **Launch the Voice Agent:**
   ```bash
   uv run python run_voice_app.py
   ```
   Opens the voice client at [http://localhost:3000/voice_client.html](http://localhost:3000/voice_client.html) and dashboard at [http://localhost:8000/dashboard](http://localhost:8000/dashboard)

## 🧪 CLI Simulation & Testing

SIVA includes a comprehensive CLI for running agent simulations and testing different scenarios using the **tau2-bench** framework.

### **Basic Simulation Commands**

**Run a single patient intake simulation:**
```bash
uv run python -m siva.cli run --domain patient_intake --agent llm_agent --user patient_intake_user_simulator --num-tasks 1 --max-steps 50
```

**Run multiple tasks for comprehensive testing:**
```bash
uv run python -m siva.cli run --domain patient_intake --agent llm_agent --user patient_intake_user_simulator --num-tasks 3 --max-steps 50
```

**Test different agent types:**
TBD.

### **Simulation Results**

After running simulations, view results with:
```bash
uv run python -m siva.cli view
```

**Example Output:**
```
╭────────────────────────────────────────── Simulation Overview ───────────────────────────────────────────╮
│ Task ID: patient_intake_PI001                                                                           │
│ Trial: 0                                                                                                │
│ Duration: 14.20s                                                                                        │
│ Termination Reason: TerminationReason.AGENT_STOP                                                         │
│ Agent Cost: $0.0218                                                                                     │
│ User Cost: $0.0021                                                                                      │
│ Reward: ✅ 1.0000 (ACTION: 1.0)                                                                         │
│                                                                                                          │
│ Action Checks:                                                                                          │
│ - 0: verify_fullname ✅ 1.0                                                                              │
│ - 1: verify_birthday ✅ 1.0                                                                              │
│ - 2: list_prescriptions ✅ 1.0                                                                           │
│ - 3: list_allergies ✅ 1.0                                                                               │
│ - 4: list_conditions ✅ 1.0                                                                              │
│ - 5: list_visit_reasons ✅ 1.0                                                                           │
│ - 6: determine_routing ✅ 1.0                                                                            │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### **Available Domains & Agents**

- **Domains**: `patient_intake`, `patient_intake-workflow`
- **Agents**: `llm_agent`, `llm_agent_solo`, `llm_agent_gt`
- **Users**: `patient_intake_user_simulator`, `dummy_user`, `user_simulator` 



## 🎯 Use Cases & Applications

### 🏥 Medical: Automated patient intake 
**Current Implementation**: Patient intake and triage with "clinical pearl" (de-identified clinical decisions and reasonings) extraction

**Key Features:**
- **Voice-driven patient intake** with symptom analysis
- **5-category routing system** (Emergency, Urgent, Routine, Self-Care, Information)
  - **🚨 Emergency**: Life-threatening conditions (chest pain, stroke signs, difficulty breathing)
  - **⚡ Urgent**: Serious but not immediately life-threatening (high fever, severe pain)
  - **📅 Routine**: Ongoing or non-urgent issues (mild symptoms, follow-ups, preventive care)
  - **🏠 Self-Care**: Minor issues manageable at home (mild cold, minor headache)
  - **ℹ️ Information**: Questions about medication, prevention, or general health advice
- **Key clinical decisions and reasoning detection** from expert corrections and conversation transcripts (aka "clinical pearls")

**Value Proposition**: Captures unwritten clinical wisdom from physician conversations with zero overhead.

## 🔄 Self-Improvement Process

![SIVA Framework Architecture](assets/flowchart_self_learning_agent.jpeg)

## 🔧 System Architecture

### Core Components
- **Frontend**: Pure HTML/JavaScript voice client with audio streaming
- **API Layer**: FastAPI routes and WebSocket handlers for communication
- **Core Logic**: Vector store + LLM judge + data manager for continuous improvement
- **Business Logic**: Modular conversation processor with domain-specific routing
- **tau2-bench Integration**: Simulation framework for dual-control agent evaluation with markdown-driven policies and task creation

### AI Models & Usage

#### **🎤 Speech Processing**
- **STT**: OpenAI Whisper v1 (`whisper-1`) - Speech to text conversion
- **TTS**: Cartesia Sonic-2 (`sonic-2`) - Natural voice synthesis

#### **🧠 Language Models**
- **Main Agent**: GPT-3.5 Turbo 1106 (`gpt-3.5-turbo-1106`) - Conversation processing with function calling
- **LLM Judge**: GPT-3.5 Turbo (`gpt-3.5-turbo`) - Feedback analysis and knowledge extraction
- **Embeddings**: text-embedding-3-small (`text-embedding-3-small`) - 1536D vectors for similarity search

## 📊 Dashboard Monitoring

Real-time dashboard tracking: total conversations, vector store size, system accuracy, route distribution, learning progress, and recent activity. Access at [http://localhost:8000/dashboard](http://localhost:8000/dashboard) (auto-opens when using `run_voice_app.py`).


## 📁 Project Structure

```
siva/
├── pyproject.toml             # Package configuration and dependencies
├── main.py                    # FastAPI server entry point
├── run_voice_app.py           # Application launcher
├── serve_client.py            # Voice client server
├── config/                    # Configuration management
│   └── settings.py            # Pydantic settings with env validation
├── frontend/                  # Static web assets
│   ├── voice_client.html      # Voice interface
│   └── dashboard.html         # Performance monitoring
├── src/siva/                  # Main application code
│   ├── agent/                 # Agent implementations
│   ├── api_service/           # API services and endpoints
│   ├── data_model/            # Data models and schemas
│   ├── domains/               # Domain-specific implementations
│   ├── environment/           # Environment and simulation logic
│   ├── evaluator/             # Evaluation and metrics
│   ├── orchestrator/          # Orchestration and workflow
│   └── utils/                 # Utility functions
├── tests/                     # Test suite
├── data/simulations/          # tau2-bench simulation data
├── assets/                    # Media files
│   ├── siva_demo_10x.gif      # Demo recording
│   └── flowchart_self_learning_agent.jpeg # Architecture overview
└── siva_data/                 # Learning database + knowledge pearls
```










**SIVA transforms voice interactions into continuously improving AI systems, capturing domain expertise and building collective intelligence across any field.**