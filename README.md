# SIVA - Self-Improving Virtual Agent

A tau2-bench inspired agent building framework for healthcare patient intake with enhanced workflow management and validation.

## Overview

SIVA is a comprehensive agent framework that implements a tau2-bench inspired approach to building conversational AI agents. The system features:

- **Structured Workflow Management**: Phased approach to patient intake with validation at each stage
- **Enhanced Function Calling**: Proper verification and validation of all collected data
- **Termination Logic**: Prevents goodbye loops and ensures proper conversation termination
- **Timeout Management**: Automatic conversation termination based on duration and inactivity
- **Escalation Handling**: Proper escalation to human agents when needed
- **Simulation Framework**: Complete tau2-bench compatible simulation infrastructure
- **Task Generation**: Automated creation of realistic patient intake scenarios

## Key Features

### 1. Workflow Phases
The patient intake process is divided into clear phases:

- **Greeting**: Initial introduction and warm welcome
- **Basic Intake**: Collect essential patient information
- **Detailed Symptoms**: Gather comprehensive symptom information
- **Routing**: Determine appropriate care route
- **Escalation**: Handle cases requiring human intervention
- **Termination**: Proper conversation conclusion

### 2. Validation System
Each piece of collected information is validated:

- **Name Validation**: Ensures first and last name are provided
- **Birthday Validation**: Checks format (YYYY-MM-DD) and reasonableness
- **Prescription Validation**: Validates medication names and dosages
- **Symptom Validation**: Ensures severity scale (1-10) and required fields
- **Routing Validation**: Validates care route selection and reasoning

### 3. Enhanced Function Calling
The system uses structured function calls with validation:

```python
# Example function call with validation
{
    "name": "verify_birthday",
    "arguments": {
        "birthday": "1990-05-15"
    }
}
```

### 4. Termination Prevention
The system prevents goodbye loops by:

- Detecting termination keywords in responses
- Using explicit termination function calls
- Implementing timeout mechanisms
- Tracking conversation state

### 5. Simulation Infrastructure
Complete tau2-bench compatible simulation system:

- **Patient Intake Domain**: Specialized environment for healthcare scenarios
- **Task Generation**: Automated creation of realistic patient scenarios
- **User Simulation**: Healthcare-specific patient behavior simulation
- **Evaluation Framework**: Comprehensive performance metrics

## Architecture

### Core Components

1. **LLMAgent**: Enhanced agent with workflow management
2. **PatientIntakeTools**: Validated tools for data collection
3. **WorkflowPhase**: Enumeration of conversation phases
4. **ValidationStatus**: Status tracking for each data field
5. **PatientData**: Structured data model with validation
6. **PatientIntakeEnvironment**: Domain-specific environment
7. **PatientIntakeUserSimulator**: Healthcare-specific user simulation

### State Management

The agent maintains comprehensive state including:

- Current workflow phase
- Patient data with validation status
- Conversation timing
- Escalation and termination reasons

## Usage

### Basic Setup

```python
from siva.agent.llm_agent import LLMAgent
from siva.domains.patient_intake.tools import create_patient_intake_tools

# Create tools
tools = create_patient_intake_tools()

# Create agent
agent = LLMAgent(
    tools=tools,
    domain_policy="path/to/policy.md",
    llm="gpt-4",
    max_conversation_duration=1800,  # 30 minutes
    max_inactivity_duration=300,     # 5 minutes
)

# Initialize state
state = agent.get_init_state()
```

### Workflow Example

```python
# 1. Greeting Phase
user_message = UserMessage(content="Hello, I need to schedule an appointment")
response, state = agent.generate_next_message(user_message, state)

# 2. Basic Intake Phase
user_message = UserMessage(content="My name is John Smith")
response, state = agent.generate_next_message(user_message, state)

# 3. Continue through phases...
# The agent automatically advances phases when validation is complete
```

### Validation Example

```python
# The agent will validate each response
{
    "name": "verify_fullname",
    "arguments": {
        "names": [{"first_name": "John", "last_name": "Smith"}]
    }
}

# Returns validation result
{
    "success": True,
    "message": "Stored full name: John Smith",
    "validation_status": "valid"
}
```

## Simulation and Task Creation

### Creating Patient Intake Tasks

The system includes an automated task generation system for creating realistic patient intake scenarios:

```bash
# Generate patient intake tasks
uv run python src/siva/domains/patient_intake/tasks/create_tasks.py

# This creates tasks.json with 7 realistic patient scenarios:
# - Simple scenarios (basic information collection)
# - Moderate scenarios (complex medical history)
# - Complex scenarios (challenging communication or multiple issues)
```

The task generation system creates scenarios with:
- **Realistic Patient Profiles**: Names, ages, medical histories
- **Varied Communication Styles**: Cooperative, anxious, confused, reluctant, rushed
- **Medical Complexity**: Different levels of symptoms and conditions
- **Evaluation Criteria**: Expected tool calls and validation requirements

### Running Simulations

SIVA provides a complete simulation framework for evaluating agent performance:

```bash
# Run a solo agent simulation (agent with all information upfront)
uv run python src/siva/cli_main.py run \
  --domain patient_intake \
  --num-tasks 1 \
  --num-trials 1 \
  --agent llm_agent_solo \
  --user dummy_user \
  --max-steps 10

# Run a full agent simulation with patient simulator
uv run python src/siva/cli_main.py run \
  --domain patient_intake \
  --num-tasks 1 \
  --num-trials 1 \
  --agent llm_agent \
  --user patient_intake_user_simulator \
  --max-steps 50
```

### Simulation Configuration

The simulation system supports various configurations:

```bash
# Available domains
--domain patient_intake              # Standard patient intake
--domain patient_intake-workflow     # Workflow-based patient intake

# Available agents
--agent llm_agent                    # Full conversational agent
--agent llm_agent_solo              # Solo agent (all info upfront)
--agent llm_agent_gt                # Agent with oracle plan

# Available users
--user dummy_user                    # Simple dummy user
--user user_simulator               # Generic user simulator
--user patient_intake_user_simulator # Healthcare-specific patient simulator

# Task selection
--task-set-name patient_intake       # Default task set
--task-set-name patient_intake_full  # Full task set
--task-set-name patient_intake_small # Small task set
--task-ids PI001 PI002              # Specific task IDs
--num-tasks 5                       # Number of tasks to run
```

### Simulation Results

Simulations generate comprehensive results including:

- **Performance Metrics**: Reward scores, pass rates, costs
- **Action Evaluation**: Tool call success rates
- **Conversation Analysis**: Duration, termination reasons
- **Detailed Logs**: Complete conversation transcripts

Results are saved to `data/siva/simulations/` with timestamps.

### Patient Intake User Simulator

The system includes a specialized patient simulator that:

- **Generates Realistic Responses**: Based on patient profiles and communication styles
- **Handles Medical Information**: Names, birthdays, prescriptions, allergies, conditions
- **Simulates Communication Styles**: Cooperative, anxious, confused, reluctant, rushed
- **Provides Contextual Responses**: Tailored to the specific patient scenario

## Configuration

### Environment Variables

```bash
export OPENAI_API_KEY="your-api-key"
export VECTOR_STORE_PATH="path/to/vector/store"
export LLM_MODEL="gpt-4"
```

### Policy Configuration

The system uses markdown policy files that define:

- Agent behavior and responsibilities
- Workflow phases and requirements
- Validation rules
- Escalation criteria

### Database Configuration

Patient intake specific data is configured in:

- **`data/siva/domains/patient_intake/db.toml`**: System configuration, medical data, validation rules
- **`data/siva/domains/patient_intake/user_db.toml`**: Patient-specific information and preferences

## Testing

### Running Tests

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest tests/

# Run specific test
uv run pytest tests/test_agent.py -k "test_workflow_validation"
```

### Test Coverage

The test suite covers:

- Workflow phase transitions
- Data validation
- Function calling
- Termination logic
- Timeout handling
- Simulation infrastructure
- Task generation

## Troubleshooting

### Common Issues

1. **Goodbye Loop**: Ensure termination function is called properly
2. **Incomplete Data**: Check validation status for each field
3. **Phase Stuck**: Verify all required fields are validated
4. **Timeout Issues**: Adjust conversation and inactivity durations
5. **Simulation Errors**: Check API keys and task configuration
6. **Task Generation**: Ensure all required data files are present

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see tau2-bench's LICENSE file for details.

## Acknowledgments

- Inspired by [tau2-bench](https://github.com/sierra-research/tau2-bench)
- Built with modern Python practices
- Enhanced for healthcare applications
