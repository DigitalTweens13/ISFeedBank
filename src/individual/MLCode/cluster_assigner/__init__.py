"""Прототип компонента «Назначение кластера» воркера разметки (ЛР № 3, уровень L4)."""

from .assigner import ClusterAssigner
from .models import ClusterAssignment, ClusterCatalog, ClusterMatch, Matrix, ReferenceSet
from .registry import StrategyRegistry
from .strategies import (
    ClusterAssignmentStrategy,
    CosineCentroidStrategy,
    FaissCentroidStrategy,
    KnnVotingStrategy,
)

__all__ = [
    "ClusterAssigner",
    "ClusterAssignment",
    "ClusterAssignmentStrategy",
    "ClusterCatalog",
    "ClusterMatch",
    "CosineCentroidStrategy",
    "FaissCentroidStrategy",
    "KnnVotingStrategy",
    "Matrix",
    "ReferenceSet",
    "StrategyRegistry",
]
