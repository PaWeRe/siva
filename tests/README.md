# SIVA Learning System Test Suite

This directory contains comprehensive testing tools for validating the SIVA learning system's progression, accuracy, and readiness capabilities.

## 🧪 Test Components

### 1. Patient Scenarios (`simulations/patient_scenarios.py`)
Comprehensive collection of realistic patient scenarios covering all route types:

- **Emergency (3 scenarios)**: Heart attack, stroke, severe allergic reaction
- **Urgent (3 scenarios)**: High fever, severe abdominal pain, chest pain  
- **Routine (3 scenarios)**: Annual physical, follow-up visits, mild issues
- **Self-Care (3 scenarios)**: Common cold, minor headache, digestive upset
- **Information (2 scenarios)**: Medication questions, preventive care

### 2. Learning Test Framework (`simulations/learning_test_framework.py`)
Advanced testing framework that:

- Simulates realistic patient conversations
- Tracks learning progression over time
- Measures accuracy improvements
- Calculates system readiness scores
- Provides detailed analytics and reporting

### 3. CLI Test Runner (`run_learning_tests.py`)
Easy-to-use command-line interface for running tests:

```bash
# View available scenarios
uv run python tests/run_learning_tests.py --test-type demo

# Run quick learning test (2 rounds, 3 scenarios each)
uv run python tests/run_learning_tests.py --test-type quick

# Run comprehensive test (5 rounds, 8 scenarios each)  
uv run python tests/run_learning_tests.py --test-type comprehensive

# Test specific scenario
uv run python tests/run_learning_tests.py --test-type scenario --scenario "Acute Myocardial Infarction"

# Run accuracy validation
uv run python tests/run_learning_tests.py --test-type accuracy
```

## 📊 What Gets Tested

### Learning Progression
- **Vector Store Growth**: Tracks how the system accumulates knowledge
- **Accuracy Improvement**: Measures prediction accuracy over time
- **Route Coverage**: Ensures diverse case representation
- **Processing Efficiency**: Monitors conversation handling speed

### System Readiness
Comprehensive readiness scoring based on:

- **Data Readiness (30%)**: Vector store size and diversity
- **Accuracy Readiness (40%)**: Recent prediction accuracy
- **Coverage Readiness (20%)**: Route type diversity 
- **Stability Readiness (10%)**: System consistency

### Real-time Metrics
- Learning curves showing progression over time
- System readiness dashboard with component scoring
- Embedding visualizations showing patient clustering
- Performance analytics and recommendations

## 🎯 Key Improvements Made

### Fixed Learning Curve Issues
✅ **Before**: Learning curves showed constant values  
✅ **After**: Dynamic progression based on actual system growth

✅ **Before**: Vector size always showed [0,0]  
✅ **After**: Real-time tracking of vector store growth

✅ **Before**: No system readiness indication  
✅ **After**: Comprehensive readiness scoring with recommendations

### Enhanced Visualization  
✅ **Before**: Static embedding views  
✅ **After**: Interactive clustering with PCA/t-SNE views

✅ **Before**: Limited learning metrics  
✅ **After**: Multi-dimensional readiness assessment

## 🚀 Usage Examples

### Quick System Validation
```bash
# Test if learning system is working
uv run python tests/run_learning_tests.py --test-type quick --save-results
```

### Comprehensive Learning Analysis
```bash
# Full system capability assessment
uv run python tests/run_learning_tests.py --test-type comprehensive --save-results
```

### Individual Scenario Testing
```bash
# Test specific case types
uv run python tests/run_learning_tests.py --test-type scenario --scenario "Stroke Symptoms"
```

## 📈 Interpreting Results

### Learning Curve Metrics
- **Accuracy**: Should improve from ~65% to 90%+ as system learns
- **Vector Size**: Should grow linearly with each conversation
- **Timestamps**: Show real learning progression over time

### System Readiness Scores
- **0-30**: Not ready - needs more data and training
- **30-60**: Developing - basic functionality present
- **60-80**: Good - ready for supervised use  
- **80-100**: Excellent - ready for production

### Recommendations
The system provides specific recommendations based on readiness components:
- Data collection needs
- Accuracy improvements required
- Coverage gaps to address
- Stability enhancements needed

## 🔧 Technical Implementation

### Test Framework Architecture
```
SIVALearningTester
├── Patient Simulation Engine
├── Metrics Calculation System  
├── Progress Tracking Database
├── Report Generation Tools
└── Results Export Functionality
```

### Data Flow
1. **Scenario Selection**: Choose diverse patient cases
2. **Conversation Simulation**: Run realistic patient interactions
3. **Metrics Collection**: Track accuracy, timing, and growth
4. **Analysis**: Calculate learning progression and readiness
5. **Reporting**: Generate comprehensive results and recommendations

This testing suite ensures SIVA's learning capabilities are thoroughly validated and continuously monitored for optimal performance.