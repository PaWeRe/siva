"""
Embedding visualization endpoints for SIVA vector store analysis.
"""

import json
import numpy as np
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.cluster import DBSCAN
import logging

router = APIRouter()


def load_vector_data() -> List[Dict[str, Any]]:
    """Load conversation vectors from the vector store."""
    try:
        with open("siva_data/conversation_vectors.json", "r") as f:
            data = json.load(f)
            return data.get("conversations", [])
    except Exception as e:
        logging.error(f"Error loading vector data: {e}")
        return []


def reduce_embeddings(embeddings: np.ndarray, method: str = "pca") -> np.ndarray:
    """Reduce embeddings to 2D for visualization."""
    if method == "pca":
        reducer = PCA(n_components=2, random_state=42)
    elif method == "tsne":
        reducer = TSNE(
            n_components=2, random_state=42, perplexity=min(30, len(embeddings) - 1)
        )
    else:
        raise ValueError(f"Unknown reduction method: {method}")

    return reducer.fit_transform(embeddings)


def cluster_embeddings(
    embeddings: np.ndarray, eps: float = 0.5, min_samples: int = 2
) -> np.ndarray:
    """Cluster embeddings using DBSCAN."""
    clusterer = DBSCAN(eps=eps, min_samples=min_samples)
    return clusterer.fit_predict(embeddings)


@router.get("/embedding_visualization")
async def get_embedding_visualization(
    method: str = "pca", include_clusters: bool = True
):
    """
    Get 2D embedding visualization data for the vector store.

    Args:
        method: Dimensionality reduction method ('pca' or 'tsne')
        include_clusters: Whether to include cluster assignments
    """
    try:
        conversations = load_vector_data()

        if not conversations:
            return {"error": "No conversation data found", "data": []}

        # Extract embeddings and metadata
        embeddings = []
        metadata = []

        for conv in conversations:
            if "embedding" in conv and conv["embedding"]:
                embeddings.append(conv["embedding"])
                metadata.append(
                    {
                        "id": conv.get("id", "unknown"),
                        "route": conv.get("correct_route", "unknown"),
                        "symptoms": (
                            conv.get("symptoms_summary", "")[:100] + "..."
                            if len(conv.get("symptoms_summary", "")) > 100
                            else conv.get("symptoms_summary", "")
                        ),
                        "timestamp": conv.get("timestamp", ""),
                    }
                )

        if len(embeddings) < 2:
            return {"error": "Need at least 2 embeddings for visualization", "data": []}

        # Convert to numpy array
        embeddings_array = np.array(embeddings)

        # Reduce dimensions
        reduced_embeddings = reduce_embeddings(embeddings_array, method)

        # Cluster if requested
        clusters = None
        if include_clusters and len(embeddings) >= 3:
            clusters = cluster_embeddings(embeddings_array)

        # Prepare visualization data
        viz_data = []
        route_colors = {
            "emergency": "#dc3545",
            "urgent": "#fd7e14",
            "routine": "#28a745",
            "self_care": "#17a2b8",
            "information": "#6f42c1",
            "unknown": "#6c757d",
        }

        for i, (x, y) in enumerate(reduced_embeddings):
            point = {
                "x": float(x),
                "y": float(y),
                "id": metadata[i]["id"],
                "route": metadata[i]["route"],
                "symptoms": metadata[i]["symptoms"],
                "timestamp": metadata[i]["timestamp"],
                "color": route_colors.get(metadata[i]["route"], "#6c757d"),
                "cluster": int(clusters[i]) if clusters is not None else -1,
            }
            viz_data.append(point)

        # Calculate cluster statistics
        cluster_stats = {}
        if clusters is not None:
            unique_clusters = np.unique(clusters)
            for cluster_id in unique_clusters:
                if cluster_id == -1:
                    continue  # Skip noise points
                cluster_points = [p for p in viz_data if p["cluster"] == cluster_id]
                route_counts = {}
                for point in cluster_points:
                    route = point["route"]
                    route_counts[route] = route_counts.get(route, 0) + 1

                cluster_stats[int(cluster_id)] = {
                    "size": len(cluster_points),
                    "routes": route_counts,
                    "dominant_route": (
                        max(route_counts.items(), key=lambda x: x[1])[0]
                        if route_counts
                        else "unknown"
                    ),
                }

        return {
            "method": method,
            "total_points": len(viz_data),
            "data": viz_data,
            "cluster_stats": cluster_stats,
            "route_colors": route_colors,
        }

    except Exception as e:
        logging.error(f"Error creating embedding visualization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/embedding_analysis")
async def get_embedding_analysis():
    """Get detailed analysis of the embedding space."""
    try:
        conversations = load_vector_data()

        if not conversations:
            return {"error": "No conversation data found"}

        # Group by route
        route_groups = {}
        for conv in conversations:
            route = conv.get("correct_route", "unknown")
            if route not in route_groups:
                route_groups[route] = []
            route_groups[route].append(conv)

        # Calculate statistics
        analysis = {
            "total_conversations": len(conversations),
            "route_distribution": {},
            "embedding_statistics": {},
        }

        for route, convs in route_groups.items():
            analysis["route_distribution"][route] = {
                "count": len(convs),
                "percentage": (len(convs) / len(conversations)) * 100,
                "examples": [
                    {
                        "symptoms": (
                            conv.get("symptoms_summary", "")[:80] + "..."
                            if len(conv.get("symptoms_summary", "")) > 80
                            else conv.get("symptoms_summary", "")
                        ),
                        "timestamp": conv.get("timestamp", ""),
                    }
                    for conv in convs[:3]  # Show first 3 examples
                ],
            }

        # Calculate embedding space statistics
        embeddings = [
            conv["embedding"]
            for conv in conversations
            if "embedding" in conv and conv["embedding"]
        ]
        if embeddings:
            embeddings_array = np.array(embeddings)
            analysis["embedding_statistics"] = {
                "dimensions": embeddings_array.shape[1],
                "mean_magnitude": float(
                    np.mean(np.linalg.norm(embeddings_array, axis=1))
                ),
                "std_magnitude": float(
                    np.std(np.linalg.norm(embeddings_array, axis=1))
                ),
            }

        return analysis

    except Exception as e:
        logging.error(f"Error creating embedding analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar_cases/{conversation_id}")
async def get_similar_cases(conversation_id: int, limit: int = 5):
    """Get the most similar cases to a given conversation."""
    try:
        conversations = load_vector_data()

        # Find the target conversation
        target_conv = None
        for conv in conversations:
            if conv.get("id") == conversation_id:
                target_conv = conv
                break

        if not target_conv or "embedding" not in target_conv:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found or no embedding available",
            )

        target_embedding = np.array(target_conv["embedding"])

        # Calculate similarities
        similarities = []
        for conv in conversations:
            if conv.get("id") == conversation_id or "embedding" not in conv:
                continue

            conv_embedding = np.array(conv["embedding"])
            similarity = np.dot(target_embedding, conv_embedding) / (
                np.linalg.norm(target_embedding) * np.linalg.norm(conv_embedding)
            )

            similarities.append(
                {
                    "id": conv.get("id"),
                    "similarity": float(similarity),
                    "route": conv.get("correct_route", "unknown"),
                    "symptoms": conv.get("symptoms_summary", ""),
                    "timestamp": conv.get("timestamp", ""),
                }
            )

        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x["similarity"], reverse=True)

        return {
            "target_conversation": {
                "id": target_conv.get("id"),
                "route": target_conv.get("correct_route", "unknown"),
                "symptoms": target_conv.get("symptoms_summary", ""),
                "timestamp": target_conv.get("timestamp", ""),
            },
            "similar_cases": similarities[:limit],
        }

    except Exception as e:
        logging.error(f"Error finding similar cases: {e}")
        raise HTTPException(status_code=500, detail=str(e))
