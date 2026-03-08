import numpy as np
from sklearn.manifold import TSNE


def reduce_to_2d(
    embeddings: list[list[float]],
    query_embedding: list[float] | None = None,
) -> tuple[list[dict], dict | None]:
    """
    Reduce high-dim embeddings to 2D using t-SNE.
    Returns (chunk_points, query_point).
    Each point is {"x": float, "y": float}.
    """
    all_embs = list(embeddings)
    has_query = query_embedding is not None
    if has_query:
        all_embs.append(query_embedding)

    arr = np.array(all_embs)

    # Handle edge case: only 1 point
    if len(arr) <= 1:
        points = [{"x": 0.5, "y": 0.5}] * len(embeddings)
        qp = {"x": 0.5, "y": 0.5} if has_query else None
        return points, qp

    # t-SNE requires perplexity < n_samples
    perplexity = min(30, max(2, len(arr) - 1))
    tsne = TSNE(n_components=2, perplexity=perplexity, random_state=42)
    coords = tsne.fit_transform(arr)

    # Normalize to [0, 1] range for SVG rendering
    mins = coords.min(axis=0)
    maxs = coords.max(axis=0)
    ranges = maxs - mins
    ranges = np.where(ranges == 0, 1, ranges)
    normalized = (coords - mins) / ranges

    chunk_points = [
        {"x": round(float(normalized[i][0]), 4), "y": round(float(normalized[i][1]), 4)}
        for i in range(len(embeddings))
    ]

    query_point = None
    if has_query:
        query_point = {
            "x": round(float(normalized[-1][0]), 4),
            "y": round(float(normalized[-1][1]), 4),
        }

    return chunk_points, query_point
