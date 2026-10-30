"""Контекст паттерна «Стратегия»: точка входа компонента «Назначение кластера»."""

from __future__ import annotations

from .models import ClusterAssignment, ClusterCatalog, Matrix
from .strategies import ClusterAssignmentStrategy


class ClusterAssigner:
    """Назначает кластер эмбеддингам из BERT-инференса.

    Алгоритм поиска делегируется стратегии, которую можно заменить на ходу через
    set_strategy(). Сам контекст отвечает за проверку входа, порог выброса и
    перевод идентификатора кластера в название из справочника.
    """

    def __init__(
        self,
        strategy: ClusterAssignmentStrategy,
        catalog: ClusterCatalog,
        min_similarity: float = 0.5,
    ) -> None:
        if not -1.0 <= min_similarity <= 1.0:
            raise ValueError("min_similarity должен лежать в [-1, 1]")
        self._strategy = strategy
        self._catalog = catalog
        self._min_similarity = min_similarity

    @property
    def strategy(self) -> ClusterAssignmentStrategy:
        return self._strategy

    def set_strategy(self, strategy: ClusterAssignmentStrategy) -> None:
        self._strategy = strategy

    def assign(self, embeddings: Matrix) -> list[ClusterAssignment]:
        if embeddings.ndim != 2 or embeddings.shape[1] != self._catalog.dim:
            raise ValueError(
                f"ожидается батч (n, {self._catalog.dim}), получено {embeddings.shape}"
            )
        matches = self._strategy.assign(embeddings)
        return [self._to_assignment(m.cluster_id, m.score) for m in matches]

    def _to_assignment(self, cluster_id: int, score: float) -> ClusterAssignment:
        # Слишком далёкий от всех кластеров отзыв помечается выбросом: возможно, это новая тема.
        if score < self._min_similarity:
            return ClusterAssignment(None, None, score, self._strategy.name, is_outlier=True)
        return ClusterAssignment(
            cluster_id=cluster_id,
            cluster_name=self._catalog.name_of(cluster_id),
            score=score,
            strategy=self._strategy.name,
            is_outlier=False,
        )
