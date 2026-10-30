"""Модели данных компонента «Назначение кластера» (cluster_assigner)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

# Матрица эмбеддингов: строка — один отзыв, столбец — координата вектора BERT.
Matrix = npt.NDArray[np.float32]
IdArray = npt.NDArray[np.int64]


@dataclass(frozen=True)
class ClusterCatalog:
    """Справочник кластеров: идентификаторы, названия и центроиды.

    Центроиды строятся заранее при обучении модели и загружаются при запуске воркера.
    """

    cluster_ids: tuple[int, ...]
    names: tuple[str, ...]
    centroids: Matrix

    def __post_init__(self) -> None:
        if self.centroids.ndim != 2:
            raise ValueError("centroids должна быть матрицей (k, d)")
        if not (len(self.cluster_ids) == len(self.names) == self.centroids.shape[0]):
            raise ValueError("число идентификаторов, названий и центроидов не совпадает")
        if len(set(self.cluster_ids)) != len(self.cluster_ids):
            raise ValueError("идентификаторы кластеров должны быть уникальными")

    @property
    def dim(self) -> int:
        return int(self.centroids.shape[1])

    def name_of(self, cluster_id: int) -> str:
        return self.names[self.cluster_ids.index(cluster_id)]


@dataclass(frozen=True)
class ReferenceSet:
    """Эталонные отзывы с известным кластером, нужны стратегии k ближайших соседей."""

    embeddings: Matrix
    cluster_ids: IdArray

    def __post_init__(self) -> None:
        if self.embeddings.ndim != 2 or self.embeddings.shape[0] != self.cluster_ids.shape[0]:
            raise ValueError("embeddings (n, d) и cluster_ids (n,) не согласованы")
        if self.embeddings.shape[0] == 0:
            raise ValueError("эталонный набор пуст")


@dataclass(frozen=True)
class ClusterMatch:
    """Ответ стратегии для одного отзыва.

    score — косинусная близость в диапазоне [-1, 1]; это общий контракт всех стратегий,
    поэтому порог выброса в ClusterAssigner одинаково работает с любой из них.
    """

    cluster_id: int
    score: float


@dataclass(frozen=True)
class ClusterAssignment:
    """Итог назначения кластера, который передаётся валидатору разметки."""

    cluster_id: int | None
    cluster_name: str | None
    score: float
    strategy: str
    is_outlier: bool
