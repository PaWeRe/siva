"""
SIVA Framework Demonstration.

Shows how to use the framework for different applications.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from applications.patient_intake import PatientIntakeApp
from applications.clinical_pearls import ClinicalPearlsApp


def demo_patient_intake():
    """Demonstrate patient intake application."""
    print("=== SIVA Patient Intake Demo ===\n")

    # Initialize patient intake app
    app = PatientIntakeApp()

    # Simulate patient interaction
    patient_data = {
        "intent": "seek_care",
        "data": {
            "symptoms": ["chest pain", "shortness of breath"],
            "duration": "30 minutes",
            "severity": "moderate",
        },
        "confidence": 0.9,
    }

    # Process interaction (simulating voice input)
    print(
        "Patient: 'I'm having chest pain and trouble breathing for the last 30 minutes'"
    )

    # Simulate the framework processing
    experience_evidence = []  # No similar cases yet

    # Get domain evidence from simulated OpenEvidence
    domain_evidence = app.domain_knowledge.get_domain_evidence(patient_data)

    # Make decision
    decision = app._make_decision(experience_evidence, domain_evidence)

    print(f"\nAI Decision: {decision['route']}")
    print(f"Reasoning: {decision['reasoning']}")
    print(f"Confidence: {decision['confidence']:.2f}")

    # Simulate human feedback
    print("\n--- Human Expert Feedback ---")
    print(
        "Expert: 'This should be emergency care - chest pain with shortness of breath requires immediate evaluation'"
    )

    feedback_result = app.handle_patient_feedback(
        "session_001",
        "emergency",
        "Chest pain with shortness of breath requires immediate cardiac evaluation",
    )

    print(f"Knowledge Updated: {feedback_result['knowledge_updated']}")


def demo_clinical_pearls():
    """Demonstrate clinical pearls application."""
    print("\n=== SIVA Clinical Pearls Demo ===\n")

    # Initialize clinical pearls app
    app = ClinicalPearlsApp()

    # Simulate physician interaction
    print(
        "Physician: 'For this UTI case, I'm considering nitrofurantoin instead of cipro due to pregnancy risk'"
    )

    # Extract clinical pearl
    pearl_result = app.extract_clinical_pearl(
        "Use nitrofurantoin for UTI in pregnancy-risk patients",
        "Nitrofurantoin is safer in pregnancy than fluoroquinolones like ciprofloxacin",
    )

    if pearl_result.get("extracted", False):
        pearl = pearl_result["pearl"]
        print(f"\nClinical Pearl Extracted:")
        print(f"Text: {pearl.get('text', 'N/A')}")
        print(f"Category: {pearl.get('category', 'N/A')}")
        print(f"Confidence: {pearl.get('confidence', 0):.2f}")
        print(f"Applicability: {pearl.get('applicability', 'N/A')}")

        validation = pearl_result["validation"]
        print(f"Validation Status: {validation.get('status', 'N/A')}")
        print(f"Validation Confidence: {validation.get('confidence', 0):.2f}")

    # Simulate framework processing for clinical decision
    clinical_patterns = [
        {
            "text": "UTI in pregnancy-risk patients requires careful antibiotic selection",
            "confidence": 0.8,
            "category": "treatment",
        }
    ]

    # Get domain evidence from simulated medical literature
    clinical_data = {
        "intent": "clinical_decision",
        "data": {
            "symptoms": ["UTI", "pregnancy risk"],
            "conditions": ["urinary tract infection", "pregnancy"],
        },
    }
    domain_evidence = app.domain_knowledge.get_domain_evidence(clinical_data)

    decision = app._make_decision(
        [], domain_evidence
    )  # Empty experience evidence for demo

    print(f"\nClinical Recommendation: {decision['recommendation']}")
    print(f"Reasoning: {decision['reasoning']}")
    print(f"Evidence Level: {decision['evidence_level']}")


def demo_framework_generalization():
    """Demonstrate framework generalization across domains."""
    print("\n=== Framework Generalization Demo ===\n")

    # Show how the same framework works for different applications
    print("The SIVA Framework provides:")
    print("1. Voice Interface: Universal speech processing")
    print("2. Dual-Purpose Vector Store: Confidence + enhancement")
    print("3. Domain Knowledge Adapter: Pluggable knowledge sources")
    print("4. Learning Pipeline: Universal feedback processing")
    print("5. Configuration System: Domain-specific customization")

    print("\nApplications demonstrate:")
    print("- Patient Intake: Healthcare automation with medical guidelines")
    print(
        "- Clinical Pearls: Medical intelligence collection with literature validation"
    )
    print("- Future: Educational tutoring, customer service, etc.")


if __name__ == "__main__":
    print("SIVA Framework Demonstration\n")
    print("This demo shows how the SIVA framework generalizes across domains")
    print("while providing specialized functionality for each application.\n")

    demo_patient_intake()
    demo_clinical_pearls()
    demo_framework_generalization()

    print("\n=== Demo Complete ===")
    print("The framework successfully demonstrates:")
    print("✓ Voice-driven interaction")
    print("✓ Dual-purpose retrieval (confidence + enhancement)")
    print("✓ Domain knowledge integration")
    print("✓ Continuous learning from human feedback")
    print("✓ Generalizable architecture")
