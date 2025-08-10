"""
Dual-Purpose Vector Store for SIVA Framework.

Serves both confidence assessment and few-shot enhancement purposes.
"""

import os
import json
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from openai import OpenAI
from datetime import datetime
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
from .config import RetrievalConfig


class DualPurposeVectorStore:
    """Manages case embeddings for both confidence assessment and enhancement."""

    def __init__(self, config: RetrievalConfig, data_dir: str = "siva_data"):
        self.config = config
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.data_file = self.data_dir / "case_vectors.json"
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.cases = []
        self.load_data()

    def load_data(self):
        """Load existing case data from file."""
        try:
            if self.data_file.exists():
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                    self.cases = data.get("cases", [])
                print(
                    f"[DualPurposeVectorStore] Loaded {len(self.cases)} cases from {self.data_file}"
                )
            else:
                print(
                    f"[DualPurposeVectorStore] No existing data file found at {self.data_file}"
                )
        except Exception as e:
            print(f"[DualPurposeVectorStore] Error loading data: {e}")
            self.cases = []

    def save_data(self):
        """Save case data to file."""
        try:
            data = {"cases": self.cases}
            with open(self.data_file, "w") as f:
                json.dump(data, f, indent=2)
            print(
                f"[DualPurposeVectorStore] Saved {len(self.cases)} cases to {self.data_file}"
            )
        except Exception as e:
            print(f"[DualPurposeVectorStore] Error saving data: {e}")

    def get_case_text(self, case_data: Dict[str, Any]) -> str:
        """Extract relevant text from case data for embedding."""
        # This is domain-specific and should be overridden by applications
        if "conversation_messages" in case_data:
            # Handle conversation-based cases (like patient intake)
            relevant_parts = []
            for msg in case_data["conversation_messages"]:
                content = msg.get("content") or ""
                if msg.get("role") == "user":
                    relevant_parts.append(content)
                elif msg.get("role") == "assistant":
                    relevant_parts.append(content)
            return " ".join(relevant_parts)
        elif "text" in case_data:
            # Handle simple text cases
            return case_data["text"]
        else:
            # Fallback: convert case data to string
            return str(case_data)

    def get_embedding(self, text: str) -> List[float]:
        """Get OpenAI embedding for text."""
        try:
            response = self.client.embeddings.create(
                model=self.config.embedding_model, input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[DualPurposeVectorStore] Error getting embedding: {e}")
            return []

    def add_case(self, case_data: Dict[str, Any], outcome: Optional[str] = None):
        """Add a case to the vector store."""
        case_text = self.get_case_text(case_data)

        if not case_text.strip():
            print("[DualPurposeVectorStore] Empty case text, skipping")
            return

        embedding = self.get_embedding(case_text)
        if not embedding:
            print("[DualPurposeVectorStore] Failed to get embedding, skipping")
            return

        case_entry = {
            "id": len(self.cases),
            "case_text": case_text,
            "case_data": case_data,
            "outcome": outcome,
            "embedding": embedding,
            "timestamp": datetime.now().isoformat(),
        }

        self.cases.append(case_entry)
        self.save_data()
        print(f"[DualPurposeVectorStore] Added case with outcome: {outcome}")

    def get_similar_cases(
        self, current_case: Dict[str, Any], k: Optional[int] = None
    ) -> List[Tuple[Dict, float]]:
        """Retrieve similar cases with similarity scores."""
        if not self.cases:
            print("[DualPurposeVectorStore] No cases in store")
            return []

        k = k or self.config.max_retrieved_cases
        current_text = self.get_case_text(current_case)

        if not current_text.strip():
            print("[DualPurposeVectorStore] Empty current case text")
            return []

        current_embedding = self.get_embedding(current_text)
        if not current_embedding:
            print("[DualPurposeVectorStore] Failed to get current embedding")
            return []

        similarities = []
        for case in self.cases:
            if case.get("embedding"):
                sim_score = cosine_similarity([current_embedding], [case["embedding"]])[
                    0
                ][0]
                similarities.append((case, sim_score))

        # Sort by similarity (highest first) and filter by threshold
        similarities.sort(key=lambda x: x[1], reverse=True)
        similar_cases = [
            (case, score)
            for case, score in similarities
            if score >= self.config.similarity_threshold
        ]

        print(
            f"[DualPurposeVectorStore] Found {len(similar_cases)} similar cases above threshold {self.config.similarity_threshold}"
        )
        return similar_cases[:k]

    def assess_confidence(self, similar_cases: List[Tuple[Dict, float]]) -> float:
        """Assess confidence based on number of similar cases."""
        # Simple confidence metric: more similar cases = higher confidence
        num_similar = len(similar_cases)
        if num_similar >= self.config.min_cases_for_confidence:
            # High confidence if we have enough similar cases
            return min(1.0, num_similar / (self.config.min_cases_for_confidence * 2))
        else:
            # Low confidence if we don't have enough similar cases
            return num_similar / self.config.min_cases_for_confidence

    def get_few_shot_examples(self, similar_cases: List[Tuple[Dict, float]]) -> str:
        """Format retrieved cases for few-shot prompting."""
        if not similar_cases:
            return ""

        examples = []
        for i, (case, score) in enumerate(similar_cases, 1):
            outcome = case.get("outcome", "unknown")
            example = f"Case {i}: {case['case_text'][:100]}... → Outcome: {outcome}"
            examples.append(example)

        return "\n".join(examples)

    def count_similar_cases(self, current_case: Dict[str, Any]) -> int:
        """Count number of similar cases above threshold (for confidence assessment)."""
        similar_cases = self.get_similar_cases(current_case)
        return len(similar_cases)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        if not self.cases:
            return {"total_cases": 0, "outcomes": {}}

        outcome_counts = {}
        for case in self.cases:
            outcome = case.get("outcome", "unknown")
            outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1

        return {
            "total_cases": len(self.cases),
            "outcomes": outcome_counts,
            "similarity_threshold": self.config.similarity_threshold,
            "min_cases_for_confidence": self.config.min_cases_for_confidence,
        }
