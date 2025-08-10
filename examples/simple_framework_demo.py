"""
Simple SIVA Framework Demonstration.

Shows the framework structure without requiring API keys.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from framework.config import SIVAConfig, VoiceConfig, RetrievalConfig, DomainConfig, LearningConfig


def demo_framework_structure():
    """Demonstrate the framework structure and configuration."""
    print("=== SIVA Framework Structure Demo ===\n")
    
    # Show how to create configurations for different domains
    print("1. Patient Intake Configuration:")
    patient_config = SIVAConfig(
        voice=VoiceConfig(
            personality="caring_healthcare_assistant",
            voice_id="5c43e078-5ba4-4e1f-9639-8d85a403f76a"
        ),
        retrieval=RetrievalConfig(
            similarity_threshold=0.75,
            min_cases_for_confidence=3
        ),
        domain=DomainConfig(
            knowledge_source="openevidence_api",
            api_key_env_var="OPENEVIDENCE_API_KEY"
        ),
        learning=LearningConfig(
            escalation_threshold=0.6
        )
    )
    
    print(f"   Voice Personality: {patient_config.voice.personality}")
    print(f"   Similarity Threshold: {patient_config.retrieval.similarity_threshold}")
    print(f"   Knowledge Source: {patient_config.domain.knowledge_source}")
    print(f"   Escalation Threshold: {patient_config.learning.escalation_threshold}")
    
    print("\n2. Clinical Pearls Configuration:")
    clinical_config = SIVAConfig(
        voice=VoiceConfig(
            personality="clinical_decision_support",
            temperature=0.2
        ),
        retrieval=RetrievalConfig(
            similarity_threshold=0.8,
            min_cases_for_confidence=5
        ),
        domain=DomainConfig(
            knowledge_source="medical_literature",
            api_key_env_var="OPENEVIDENCE_API_KEY",
            validation_enabled=True
        ),
        learning=LearningConfig(
            escalation_threshold=0.7,
            auto_extract_insights=True,
            validation_required=True
        )
    )
    
    print(f"   Voice Personality: {clinical_config.voice.personality}")
    print(f"   Similarity Threshold: {clinical_config.retrieval.similarity_threshold}")
    print(f"   Knowledge Source: {clinical_config.domain.knowledge_source}")
    print(f"   Validation Enabled: {clinical_config.domain.validation_enabled}")
    print(f"   Auto Extract Insights: {clinical_config.learning.auto_extract_insights}")


def demo_framework_components():
    """Demonstrate the framework components."""
    print("\n=== Framework Components ===\n")
    
    components = [
        ("Voice Interface", "Universal speech processing and intent extraction"),
        ("Dual-Purpose Vector Store", "Confidence assessment + few-shot enhancement"),
        ("Domain Knowledge Adapter", "Pluggable integration with external knowledge"),
        ("Learning Pipeline", "Automatic knowledge extraction from human feedback"),
        ("Configuration System", "Domain-specific customization without code changes")
    ]
    
    for i, (component, description) in enumerate(components, 1):
        print(f"{i}. {component}")
        print(f"   {description}")


def demo_applications():
    """Demonstrate framework applications."""
    print("\n=== Framework Applications ===\n")
    
    applications = [
        ("Patient Intake", "Healthcare patient routing with medical guidelines"),
        ("Clinical Pearls", "Medical intelligence collection with literature validation"),
        ("Educational Tutoring", "Student learning support with pedagogical knowledge"),
        ("Customer Service", "Support automation with product knowledge"),
        ("Legal Assistance", "Case analysis with legal precedent knowledge")
    ]
    
    for i, (app, description) in enumerate(applications, 1):
        print(f"{i}. {app}")
        print(f"   {description}")


def demo_mcmc_analogy():
    """Demonstrate the MCMC analogy."""
    print("\n=== MCMC Analogy ===\n")
    
    print("The framework operates like Markov Chain Monte Carlo:")
    print("• Sampling: Each human interaction = sample from 'true' decision distribution")
    print("• Convergence: More samples = better approximation of optimal patterns")
    print("• Confidence: Higher confidence = closer to true distribution")
    print("• Ground Truth: Human feedback guides convergence toward target patterns")


def demo_value_proposition():
    """Demonstrate the value proposition."""
    print("\n=== Value Proposition for Open Evidence ===\n")
    
    print("The framework demonstrates:")
    print("1. Generalizable Innovation: Voice-driven self-improving systems work across domains")
    print("2. Medical Specialization: Clinical pearls as sophisticated domain application")
    print("3. Proven Architecture: Dual-purpose retrieval + human feedback = reliable learning")
    print("4. Scalable Approach: Framework can be applied to other medical AI applications")


if __name__ == "__main__":
    print("SIVA Framework Structure Demonstration\n")
    print("This demo shows the framework architecture and configuration")
    print("without requiring API keys or external services.\n")
    
    demo_framework_structure()
    demo_framework_components()
    demo_applications()
    demo_mcmc_analogy()
    demo_value_proposition()
    
    print("\n=== Demo Complete ===")
    print("The framework successfully demonstrates:")
    print("✓ Configuration-driven architecture")
    print("✓ Domain-specific customization")
    print("✓ Reusable components")
    print("✓ Generalizable patterns")
    print("✓ Medical AI specialization")
    
    print("\nNext steps:")
    print("1. Add API keys to .env file")
    print("2. Run full framework demo: python examples/framework_demo.py")
    print("3. Implement OpenEvidence API integration")
    print("4. Add clinical pearl validation pipeline") 