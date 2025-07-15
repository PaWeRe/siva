# SIVA - Self-Improving Voice Agent for Patient Intake

A **self-improving** voice agent for patient intake that learns from every conversation. Features voice-driven data collection with intelligent routing decisions and automatic escalation to human staff when needed.

## 🚀 Quick Start

**Requirements:** Python 3.10+, [uv](https://docs.astral.sh/uv/) package manager, browser with microphone access

1. **Setup Environment:**
   ```bash
   uv venv .venv && source .venv/bin/activate
   uv pip install -r siva/requirements.txt
   ```

2. **Configure API Keys** (`.env` file in `siva/` directory):
   ```
   OPENAI_API_KEY=sk-your-key-here
   CARTESIA_API_KEY=your-cartesia-key-here
   ```

3. **Launch the Voice Agent:**
   ```bash
   cd siva
   python run_voice_app.py
   ```
   Opens the voice client at [http://localhost:3000/voice_client.html](http://localhost:3000/voice_client.html)

## 🎯 How It Works

1. **Voice Interaction**: Click the call button or press spacebar to start talking
2. **Data Collection**: Agent guides patients through intake questions (name, symptoms, medical history)
3. **Intelligent Routing**: Uses vector similarity search to find similar past cases and route to one of 5 care levels
4. **Learning**: When uncertain (< 3 similar cases), escalates to human and learns from the feedback
5. **Improvement**: Each human interaction improves future routing accuracy

## 🏥 5-Category Routing System

SIVA routes patients to appropriate care levels based on symptom analysis:

- **🚨 Emergency**: Life-threatening conditions (chest pain, stroke signs, difficulty breathing)
- **⚡ Urgent**: Serious but not immediately life-threatening (high fever, severe pain)
- **📅 Routine**: Ongoing or non-urgent issues (mild symptoms, follow-ups, preventive care)
- **🏠 Self-Care**: Minor issues manageable at home (mild cold, minor headache)
- **ℹ️ Information**: Questions about medication, prevention, or general health advice

## 🧠 Self-Improvement Features

### Dual-Purpose Vector Retrieval
The system uses **vector similarity search** powered by **OpenAI text-embedding-3-small** for two critical purposes:
1. **Few-Shot Prompting**: When confident (≥3 similar cases with >0.75 cosine similarity), provides relevant examples to improve routing accuracy
2. **Confidence Guardrail**: When uncertain (<3 similar cases), automatically escalates to ensure patient safety

### Learning Architecture
- **Vector-Based Learning**: 
  - Converts conversations to 1536-dimensional embeddings using text-embedding-3-small
  - Stores in persistent JSON format with metadata (symptoms, routes, timestamps)
  - Uses cosine similarity (scikit-learn) for efficient retrieval
- **LLM Judge Data Curation**:
  - GPT-3.5 Turbo extracts structured symptom summaries from raw conversations
  - Evaluates prediction accuracy and identifies learning opportunities
  - Creates training examples linking symptoms → correct routes
- **Automatic Escalation**: Routes to humans when vector similarity falls below threshold
- **Performance Tracking**: Monitors routing accuracy and escalation rates over time
- **Learning Dashboard**: Visual interface to track system improvement ([dashboard.html](dashboard.html))

## 💼 Customer Value for Healthcare Facilities

### Why Hospitals & Diagnostic Centers Need Self-Improving Systems

**High-Stakes Decision Making**: Patient routing affects safety and outcomes - incorrect triage can be life-threatening

**Resource Optimization**: Expert nurses/doctors spend hours on repetitive intake calls that could be automated

**Natural Cold-Start Handling**: Unlike traditional AI systems requiring massive upfront training:
- ✅ Starts conservative (escalates uncertain cases to humans)
- ✅ Gradually builds competence from real interactions
- ✅ Learns facility-specific patterns and patient populations
- ✅ Adapts to new symptoms/conditions without retraining

**Scalable Learning**: Each escalation improves the system for all future similar cases, creating exponential value

**Quality Assurance**: Human oversight ensures accuracy while building training data

## 🔧 System Architecture

### Core Components
- **Frontend**: Pure HTML/JavaScript voice client with real-time audio streaming
- **Backend**: FastAPI server with conversational state management
- **Learning Stack**: Vector store + LLM judge + data manager for continuous improvement

### AI Models & Usage

#### **🎤 Speech Processing**
- **STT**: OpenAI **Whisper v1** (`whisper-1`) - Converts patient speech to text with high accuracy
- **TTS**: Cartesia **Sonic-2** (`sonic-2`) - Natural voice synthesis for agent responses

#### **🧠 Language Models**
- **Main Conversation Agent**: OpenAI **GPT-3.5 Turbo 1106** (`gpt-3.5-turbo-1106`)
  - **Function Calling**: Structured data extraction (name, symptoms, medical history)
  - **State Management**: Progressive conversation phases (intake → symptoms → routing)
  - **Routing Decisions**: Final triage recommendations with reasoning
  - **Temperature**: 0.3 (balanced accuracy/creativity), Max tokens: 300

- **LLM Judge**: OpenAI **GPT-3.5 Turbo** (`gpt-3.5-turbo`)
  - **Symptom Summarization**: Extracts key medical info from conversations (temp: 0.1, tokens: 150)
  - **Prediction Analysis**: Evaluates routing accuracy and learning opportunities (temp: 0.3, tokens: 100)
  - **Data Curation**: Transforms conversations into structured training examples

#### **🔍 Vector Similarity System**
- **Embedding Model**: OpenAI **text-embedding-3-small** (`text-embedding-3-small`)
  - **Purpose**: Converts conversations to 1536-dimensional vectors for similarity search
  - **Similarity Computation**: Cosine similarity via scikit-learn
  - **Threshold**: 0.75 minimum similarity for "similar cases"
  - **Retrieval**: Top-5 similar cases for few-shot prompting

#### **Model Orchestration by Stage**
1. **Voice Input**: Whisper v1 → Text
2. **Conversation**: GPT-3.5 Turbo 1106 (with function calling) → Structured responses
3. **Symptom Analysis**: text-embedding-3-small → Vector representations
4. **Similarity Search**: Cosine similarity → Confidence determination
5. **Routing Decision**: GPT-3.5 Turbo 1106 (with few-shot examples) → Care level
6. **Voice Output**: Cartesia Sonic-2 → Natural speech
7. **Learning**: GPT-3.5 Turbo (LLM Judge) → Training data curation

## 🔄 System Flow Diagram

![SIVA Self-Learning Agent Architecture](assets/flowchart_self_learning_agent.jpeg)

The diagram above shows SIVA's complete architecture, highlighting:

- **State-Based Conversation**: Progressive phases from basic intake → detailed symptoms → routing
- **Dual-Purpose Vector Retrieval**: Serves both as confidence measure and few-shot prompt source
- **Human-in-the-Loop Learning**: Escalations become training data for future improvements
- **LLM Judge Curation**: Transforms conversations into structured learning examples
- **Continuous Improvement**: Each case strengthens the vector store for better future decisions

**Key Innovation**: The same retrieval mechanism that determines confidence (≥3 similar cases) also provides relevant examples for improved decision-making, creating an elegant self-improving feedback loop.

## 🛠 Development & Testing

**Debug Conversations** (without voice):
```bash
python debug_conversation.py
```

**Learning Progression Demo**:
```bash
python learning_demo.py
```

**Separate Server Mode**:
```bash
# Terminal 1 - Backend
uvicorn main:app --host localhost --port 8000 --reload

# Terminal 2 - Voice Client  
python serve_client.py
```

## 📊 Key Metrics

The system tracks:
- **Routing Accuracy**: Correct department/urgency recommendations
- **Escalation Rate**: Percentage of cases requiring human intervention
- **Learning Progress**: Improvement in confidence over time
- **Conversation Quality**: Turn count and completion rates

## 📁 Project Structure

```
siva/
├── main.py                 # FastAPI backend
├── run_voice_app.py         # Unified launcher
├── voice_client.html        # Voice interface
├── vector_store.py          # Similarity-based retrieval
├── llm_judge.py             # Evaluation and curation
├── data_manager.py          # Persistent data storage
├── learning_demo.py         # Improvement demonstration
├── dashboard.html           # Performance monitoring
├── intake_logs/             # Conversation history
└── siva_data/              # Learning database
```

## 🎯 Use Case

Designed for healthcare facilities needing to:
- **Automate** routine patient intake conversations
- **Route** patients to appropriate care levels (routine, urgent, emergency)
- **Reduce** expert staff time on repetitive tasks
- **Maintain** high accuracy through continuous learning

The system starts conservative and becomes more confident as it learns from human feedback, ensuring patient safety while improving efficiency.
