"""LLM Judge for data curation and evaluation of routing decisions."""

import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
import os


class LLMJudge:
    """Handles evaluation and curation of routing decisions."""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def extract_symptoms_summary(self, conversation_messages: List[Dict]) -> str:
        """Extract and summarize key symptoms from conversation for training data."""

        # Find user messages about symptoms and visit reasons
        user_inputs = []
        for msg in conversation_messages:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                user_inputs.append(content)

        conversation_text = " ".join(user_inputs)

        prompt = f"""
        Extract and summarize the key medical symptoms and reasons for visit from this patient conversation:
        
        Conversation: {conversation_text}
        
        Provide a concise summary focusing on:
        - Primary symptoms
        - Severity indicators  
        - Duration
        - Associated symptoms
        
        Keep it under 100 words and focus on medical relevance.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.1,
            )

            summary = response.choices[0].message.content.strip()
            print(f"[LLMJudge] Generated symptoms summary: {summary[:50]}...")
            return summary

        except Exception as e:
            print(f"[LLMJudge] Error generating symptoms summary: {e}")
            # Fallback to basic extraction
            return self._basic_symptom_extraction(conversation_text)

    def _basic_symptom_extraction(self, conversation_text: str) -> str:
        """Fallback method for symptom extraction."""
        # Simple keyword-based extraction
        keywords = [
            "pain",
            "ache",
            "fever",
            "headache",
            "chest",
            "shortness",
            "breath",
            "dizzy",
            "nausea",
            "vomiting",
            "rash",
            "swelling",
            "cough",
        ]

        found_symptoms = []
        text_lower = conversation_text.lower()

        for keyword in keywords:
            if keyword in text_lower:
                found_symptoms.append(keyword)

        if found_symptoms:
            return f"Patient reports: {', '.join(found_symptoms[:5])}"
        else:
            return (
                conversation_text[:100] + "..."
                if len(conversation_text) > 100
                else conversation_text
            )

    def create_training_example(
        self, conversation_messages: List[Dict], agent_prediction: str, human_label: str
    ) -> Dict[str, Any]:
        """Create a structured training example from conversation and human feedback."""

        symptoms_summary = self.extract_symptoms_summary(conversation_messages)

        training_example = {
            "conversation_messages": conversation_messages,
            "symptoms_summary": symptoms_summary,
            "agent_prediction": agent_prediction,
            "correct_route": human_label,
            "prediction_correct": agent_prediction.lower() == human_label.lower(),
        }

        print(
            f"[LLMJudge] Created training example: {agent_prediction} vs {human_label}"
        )
        return training_example

    def evaluate_prediction_accuracy(
        self, agent_prediction: str, human_label: str, conversation_messages: List[Dict]
    ) -> Dict[str, Any]:
        """Evaluate the accuracy of an agent's routing prediction."""

        is_correct = agent_prediction.lower() == human_label.lower()

        # Get detailed analysis from LLM
        analysis_prompt = f"""
        Analyze this medical routing decision:
        
        Agent predicted: {agent_prediction}
        Human expert said: {human_label}
        
        Patient conversation summary: {self.extract_symptoms_summary(conversation_messages)}
        
        Provide a brief analysis (1-2 sentences) of:
        1. Whether the prediction was reasonable given the symptoms
        2. What the agent might have missed or misunderstood
        
        Be concise and focus on learning opportunities.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=100,
                temperature=0.3,
            )

            analysis = response.choices[0].message.content.strip()

        except Exception as e:
            print(f"[LLMJudge] Error generating analysis: {e}")
            analysis = f"Prediction {'correct' if is_correct else 'incorrect'}: {agent_prediction} vs {human_label}"

        import datetime

        evaluation = {
            "prediction_correct": is_correct,
            "agent_prediction": agent_prediction,
            "human_label": human_label,
            "analysis": analysis,
            "timestamp": datetime.datetime.now().isoformat(),
        }

        print(
            f"[LLMJudge] Evaluation: {'✓' if is_correct else '✗'} {agent_prediction} vs {human_label}"
        )
        return evaluation

    def analyze_system_performance(
        self, evaluations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze overall system performance from multiple evaluations."""

        if not evaluations:
            return {"total_cases": 0, "accuracy": 0.0}

        total_cases = len(evaluations)
        correct_predictions = sum(
            1 for eval in evaluations if eval.get("prediction_correct", False)
        )
        accuracy = correct_predictions / total_cases

        # Count errors by route type
        route_errors = {}
        for eval in evaluations:
            if not eval.get("prediction_correct", True):  # Focus on errors
                human_route = eval.get("human_label", "unknown")
                agent_route = eval.get("agent_prediction", "unknown")
                error_key = f"{agent_route} → {human_route}"
                route_errors[error_key] = route_errors.get(error_key, 0) + 1

        performance_summary = {
            "total_cases": total_cases,
            "correct_predictions": correct_predictions,
            "accuracy": accuracy,
            "common_errors": dict(
                sorted(route_errors.items(), key=lambda x: x[1], reverse=True)[:3]
            ),
        }

        print(
            f"[LLMJudge] System performance: {accuracy:.2%} accuracy ({correct_predictions}/{total_cases})"
        )
        return performance_summary

    def should_add_to_training(self, evaluation: Dict[str, Any]) -> bool:
        """Determine if this case should be added to training data."""
        # For now, add all cases where we have human feedback
        # Could be made more sophisticated (e.g., only add challenging cases)
        return True

    def generate_improvement_suggestions(
        self, performance: Dict[str, Any]
    ) -> List[str]:
        """Generate suggestions for improving the system based on performance data."""

        suggestions = []
        accuracy = performance.get("accuracy", 0)
        common_errors = performance.get("common_errors", {})

        if accuracy < 0.7:
            suggestions.append(
                "Consider collecting more training examples - accuracy is below 70%"
            )

        if accuracy < 0.5:
            suggestions.append(
                "Review system prompts and routing criteria - accuracy is very low"
            )

        for error_pattern, count in common_errors.items():
            if count >= 3:
                suggestions.append(
                    f"Common error pattern: {error_pattern} (occurred {count} times)"
                )

        if not suggestions:
            suggestions.append("System performing well - continue monitoring")

        return suggestions
