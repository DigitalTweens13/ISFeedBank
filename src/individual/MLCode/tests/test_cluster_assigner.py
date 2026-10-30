"""Тесты прототипа. Запуск из папки src/individual/MLCode:  python -m unittest -v"""

from __future__ import annotations

import importlib.util
import unittest

import numpy as np

from cluster_assigner import (
    ClusterAssigner,
    ClusterAssignmentStrategy,
    ClusterCatalog,
    ClusterMatch,
    CosineCentroidStrategy,
    FaissCentroidStrategy,
    KnnVotingStrategy,
    Matrix,
    ReferenceSet,
    StrategyRegistry,
)

DIM = 32
HAS_FAISS = importlib.util.find_spec("faiss") is not None


def make_catalog() -> ClusterCatalog:
    # Центроиды — базисные векторы: кластеры заведомо далеко друг от друга.
    centroids = np.eye(3, DIM, dtype=np.float32)
    return ClusterCatalog((1, 2, 3), ("A", "B", "C"), centroids)


def make_reference(catalog: ClusterCatalog) -> ReferenceSet:
    rng = np.random.default_rng(0)
    vectors = np.vstack([c + 0.05 * rng.normal(size=(5, DIM)) for c in catalog.centroids])
    labels = np.repeat(np.asarray(catalog.cluster_ids, dtype=np.int64), 5)
    return ReferenceSet(vectors.astype(np.float32), labels)


def all_strategies(catalog: ClusterCatalog) -> list[ClusterAssignmentStrategy]:
    strategies: list[ClusterAssignmentStrategy] = [
        CosineCentroidStrategy(catalog),
        KnnVotingStrategy(make_reference(catalog), k=3),
    ]
    if HAS_FAISS:
        strategies.append(FaissCentroidStrategy(catalog))
    return strategies


class FixedStrategy(ClusterAssignmentStrategy):
    """Заглушка: всегда отвечает одним и тем же кластером."""

    name = "fixed"

    def __init__(self, cluster_id: int, score: float) -> None:
        self._match = ClusterMatch(cluster_id, score)

    def assign(self, embeddings: Matrix) -> list[ClusterMatch]:
        return [self._match] * embeddings.shape[0]


class StrategyContractTest(unittest.TestCase):
    """Любая стратегия обязана соблюдать общий контракт (принцип подстановки Лисков)."""

    def setUp(self) -> None:
        self.catalog = make_catalog()
        rng = np.random.default_rng(1)
        self.batch = (self.catalog.centroids + 0.05 * rng.normal(size=(3, DIM))).astype(np.float32)

    def test_each_strategy_finds_right_cluster(self) -> None:
        for strategy in all_strategies(self.catalog):
            with self.subTest(strategy=strategy.name):
                ids = [m.cluster_id for m in strategy.assign(self.batch)]
                self.assertEqual(ids, [1, 2, 3])

    def test_scores_are_cosine_similarities(self) -> None:
        for strategy in all_strategies(self.catalog):
            with self.subTest(strategy=strategy.name):
                matches = strategy.assign(self.batch)
                self.assertEqual(len(matches), len(self.batch))
                for m in matches:
                    self.assertGreaterEqual(m.score, -1.0 - 1e-6)
                    self.assertLessEqual(m.score, 1.0 + 1e-6)


class ClusterAssignerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = make_catalog()

    def test_set_strategy_replaces_algorithm(self) -> None:
        assigner = ClusterAssigner(FixedStrategy(1, 0.9), self.catalog)
        batch = np.zeros((2, DIM), dtype=np.float32)
        self.assertEqual(assigner.assign(batch)[0].cluster_name, "A")

        assigner.set_strategy(FixedStrategy(3, 0.9))
        result = assigner.assign(batch)
        self.assertEqual([a.cluster_name for a in result], ["C", "C"])
        self.assertEqual(result[0].strategy, "fixed")

    def test_low_similarity_is_outlier(self) -> None:
        assigner = ClusterAssigner(FixedStrategy(2, 0.3), self.catalog, min_similarity=0.5)
        (assignment,) = assigner.assign(np.zeros((1, DIM), dtype=np.float32))
        self.assertTrue(assignment.is_outlier)
        self.assertIsNone(assignment.cluster_id)

    def test_wrong_dimension_rejected(self) -> None:
        assigner = ClusterAssigner(CosineCentroidStrategy(self.catalog), self.catalog)
        with self.assertRaises(ValueError):
            assigner.assign(np.zeros((1, DIM + 1), dtype=np.float32))


class StrategyRegistryTest(unittest.TestCase):
    def test_create_by_name(self) -> None:
        registry = StrategyRegistry()
        registry.register("fixed", lambda: FixedStrategy(1, 1.0))
        self.assertIsInstance(registry.create("fixed"), FixedStrategy)
        self.assertEqual(registry.names(), ["fixed"])

    def test_unknown_name_and_duplicates_rejected(self) -> None:
        registry = StrategyRegistry()
        registry.register("fixed", lambda: FixedStrategy(1, 1.0))
        with self.assertRaises(KeyError):
            registry.create("missing")
        with self.assertRaises(ValueError):
            registry.register("fixed", lambda: FixedStrategy(2, 1.0))


class ModelValidationTest(unittest.TestCase):
    def test_catalog_rejects_mismatched_sizes(self) -> None:
        with self.assertRaises(ValueError):
            ClusterCatalog((1, 2), ("A",), np.eye(2, DIM, dtype=np.float32))


if __name__ == "__main__":
    unittest.main()
