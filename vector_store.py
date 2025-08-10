"""Vector store for conversation retrieval and similarity matching."""

import os
import json
import numpy as np
from typing import List, Dict, Any, Tuple
from openai import OpenAI
from datetime import datetime
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity


class VectorStore:
    """Manages conversation embeddings for retrieval-based routing decisions."""

    def __init__(
        self,
        data_dir: str = "siva_data",
        similarity_threshold: float = 0.75,
    ):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.data_file = self.data_dir / "conversation_vectors.json"
        self.similarity_threshold = similarity_threshold
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.conversations = []
        self.load_data()

    def load_data(self):
        """Load existing conversation data from file."""
        try:
            if self.data_file.exists():
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                    self.conversations = data.get("conversations", [])
                print(
                    f"[VectorStore] Loaded {len(self.conversations)} conversations from {self.data_file}"
                )
            else:
                print(f"[VectorStore] No existing data file found at {self.data_file}")
        except Exception as e:
            print(f"[VectorStore] Error loading data: {e}")
            self.conversations = []

    def save_data(self):
        """Save conversation data to file."""
        try:
            data = {"conversations": self.conversations}
            with open(self.data_file, "w") as f:
                json.dump(data, f, indent=2)
            print(
                f"[VectorStore] Saved {len(self.conversations)} conversations to {self.data_file}"
            )
        except Exception as e:
            print(f"[VectorStore] Error saving data: {e}")

    def get_conversation_text(self, conversation_messages: List[Dict]) -> str:
        """Extract relevant text from conversation for embedding."""
        relevant_parts = []

        for msg in conversation_messages:
            content = msg.get("content") or ""  # Handle None content safely
            if msg.get("role") == "user":
                relevant_parts.append(content)
            elif msg.get("role") == "assistant" and "symptoms" in content.lower():
                # Include assistant messages that discuss symptoms
                relevant_parts.append(content)

        return " ".join(relevant_parts)

    def get_embedding(self, text: str) -> List[float]:
        """Get OpenAI embedding for text."""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small", input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[VectorStore] Error getting embedding: {e}")
            return []

    def add_labeled_case(
        self,
        conversation_messages: List[Dict],
        correct_route: str,
        symptoms_summary: str = None,
        session_id: str = None,
    ):
        """Add a human-verified conversation to the vector store."""
        conversation_text = self.get_conversation_text(conversation_messages)

        if not conversation_text.strip():
            print("[VectorStore] Empty conversation text, skipping")
            return

        # Check for duplicates if session_id is provided
        if session_id:
            for existing_conv in self.conversations:
                if existing_conv.get("session_id") == session_id:
                    print(
                        f"[VectorStore] Conversation for session {session_id} already exists, skipping"
                    )
                    return

        embedding = self.get_embedding(conversation_text)
        if not embedding:
            print("[VectorStore] Failed to get embedding, skipping")
            return

        conversation_entry = {
            "id": len(self.conversations),
            "conversation_text": conversation_text,
            "symptoms_summary": symptoms_summary or conversation_text[:200],
            "correct_route": correct_route,
            "embedding": embedding,
            "messages": conversation_messages,
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
        }

        self.conversations.append(conversation_entry)
        self.save_data()
        print(
            f"[VectorStore] Added labeled case: {correct_route} (session: {session_id})"
        )

    def retrieve_similar(
        self, current_conversation: List[Dict], k: int = 5
    ) -> List[Tuple[Dict, float]]:
        """Retrieve similar conversations with similarity scores."""
        if not self.conversations:
            print("[VectorStore] No conversations in store")
            return []

        current_text = self.get_conversation_text(current_conversation)
        if not current_text.strip():
            print("[VectorStore] Empty current conversation")
            return []

        current_embedding = self.get_embedding(current_text)
        if not current_embedding:
            print("[VectorStore] Failed to get current embedding")
            return []

        similarities = []
        for conv in self.conversations:
            if conv.get("embedding"):
                sim_score = cosine_similarity([current_embedding], [conv["embedding"]])[
                    0
                ][0]
                similarities.append((conv, sim_score))

        # Sort by similarity (highest first) and filter by threshold
        similarities.sort(key=lambda x: x[1], reverse=True)
        similar_cases = [
            (conv, score)
            for conv, score in similarities
            if score >= self.similarity_threshold
        ]

        print(
            f"[VectorStore] Found {len(similar_cases)} similar cases above threshold {self.similarity_threshold}"
        )
        return similar_cases[:k]

    def get_few_shot_examples(self, similar_cases: List[Tuple[Dict, float]]) -> str:
        """Format retrieved cases for LLM few-shot prompting."""
        if not similar_cases:
            return ""

        examples = []
        for i, (case, score) in enumerate(similar_cases, 1):
            example = (
                f"Case {i}: {case['symptoms_summary']} → Route: {case['correct_route']}"
            )
            examples.append(example)

        return "\n".join(examples)

    def count_similar_cases(self, current_conversation: List[Dict]) -> int:
        """Count number of similar cases above threshold (for guardrail decision)."""
        similar_cases = self.retrieve_similar(current_conversation)
        return len(similar_cases)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        if not self.conversations:
            return {"total_conversations": 0, "routes": {}}

        route_counts = {}
        for conv in self.conversations:
            route = conv.get("correct_route", "unknown")
            route_counts[route] = route_counts.get(route, 0) + 1

        return {"total_conversations": len(self.conversations), "routes": route_counts}
