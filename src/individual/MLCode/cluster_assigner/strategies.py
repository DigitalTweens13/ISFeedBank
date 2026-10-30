"""Стратегии назначения кластера (паттерн «Стратегия»)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict

import numpy as np
import numpy.typing as npt

from .models import ClusterCatalog, ClusterMatch, Matrix, ReferenceSet


def l2_normalize(vectors: Matrix) -> Matrix:
    """Нормирует строки матрицы, чтобы скалярное произведение стало косинусной близостью."""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    normalized: Matrix = (vectors / norms).astype(np.float32)
    return normalized


class ClusterAssignmentStrategy(ABC):
    """Общий контракт алгоритма назначения кластера.

    Реализация получает батч эмбеддингов (n, d) и возвращает ровно n ответов,
    у каждого score — косинусная близость в [-1, 1].
    """

    name: str

    @abstractmethod
    def assign(self, embeddings: Matrix) -> list[ClusterMatch]:
        """Назначает кластер каждому эмбеддингу батча."""


class CosineCentroidStrategy(ClusterAssignmentStrategy):
    """Ближайший центроид по косинусной близости. Быстрая стратегия по умолчанию."""

    name = "cosine_centroid"

    def __init__(self, catalog: ClusterCatalog) -> None:
        self._ids = np.asarray(catalog.cluster_ids, dtype=np.int64)
        self._centroids = l2_normalize(catalog.centroids)

    def assign(self, embeddings: Matrix) -> list[ClusterMatch]:
        similarity = l2_normalize(embeddings) @ self._centroids.T
        best = similarity.argmax(axis=1)
        return [
            ClusterMatch(cluster_id=int(self._ids[j]), score=float(similarity[i, j]))
            for i, j in enumerate(best)
        ]


class KnnVotingStrategy(ClusterAssignmentStrategy):
    """Голосование k ближайших эталонных отзывов.

    Устойчивее центроидов для кластеров неправильной формы, но медленнее:
    сравнивает отзыв со всем эталонным набором, а не с k центроидами.
    """

    name = "knn_voting"

    def __init__(self, reference: ReferenceSet, k: int = 5) -> None:
        if k < 1:
            raise ValueError("k должно быть не меньше 1")
        self._vectors = l2_normalize(reference.embeddings)
        self._labels = reference.cluster_ids
        self._k = min(k, int(reference.embeddings.shape[0]))

    def assign(self, embeddings: Matrix) -> list[ClusterMatch]:
        similarity = l2_normalize(embeddings) @ self._vectors.T
        neighbours = np.argsort(-similarity, axis=1)[:, : self._k]
        return [self._vote(row, idx) for row, idx in zip(similarity, neighbours)]

    def _vote(self, similarity_row: Matrix, neighbour_idx: npt.NDArray[np.intp]) -> ClusterMatch:
        # Голос соседа весит столько, какова его близость: дальний сосед влияет меньше.
        weights: dict[int, list[float]] = defaultdict(list)
        for i in neighbour_idx:
            weights[int(self._labels[i])].append(float(similarity_row[i]))
        winner = max(weights, key=lambda cid: sum(weights[cid]))
        return ClusterMatch(cluster_id=winner, score=float(np.mean(weights[winner])))


class FaissCentroidStrategy(ClusterAssignmentStrategy):
    """Ближайший центроид через индекс faiss (IndexFlatIP по нормированным векторам).

    Даёт тот же ответ, что CosineCentroidStrategy, но рассчитан на тысячи кластеров
    и поиск на GPU. Библиотека faiss подключается только при выборе этой стратегии.
    """

    name = "faiss_centroid"

    def __init__(self, catalog: ClusterCatalog) -> None:
        try:
            import faiss  # type: ignore[import-not-found, unused-ignore]
        except ImportError as exc:
            raise RuntimeError("для стратегии faiss_centroid установите пакет faiss-cpu") from exc
        self._ids = np.asarray(catalog.cluster_ids, dtype=np.int64)
        self._index = faiss.IndexFlatIP(catalog.dim)
        self._index.add(l2_normalize(catalog.centroids))

    def assign(self, embeddings: Matrix) -> list[ClusterMatch]:
        scores, positions = self._index.search(l2_normalize(embeddings), 1)
        return [
            ClusterMatch(cluster_id=int(self._ids[pos[0]]), score=float(score[0]))
            for score, pos in zip(scores, positions)
        ]
