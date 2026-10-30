"""Демонстрация подмены стратегии назначения кластера.

Запуск из папки src/individual/MLCode:  python demo.py
Эмбеддинги синтетические (размерность 768, как у BERT-base): в воркере их выдаёт BERT-инференс.
"""

from __future__ import annotations

import numpy as np

from cluster_assigner import (
    ClusterAssigner,
    ClusterAssignment,
    ClusterCatalog,
    CosineCentroidStrategy,
    FaissCentroidStrategy,
    KnnVotingStrategy,
    Matrix,
    ReferenceSet,
    StrategyRegistry,
)

DIM = 768
CLUSTERS = {101: "Мобильное приложение", 102: "Ипотека", 103: "Карты и кешбэк"}


def make_data(rng: np.random.Generator) -> tuple[ClusterCatalog, ReferenceSet, Matrix, list[str]]:
    ids = tuple(CLUSTERS)
    centroids = rng.normal(size=(len(ids), DIM)).astype(np.float32)
    catalog = ClusterCatalog(ids, tuple(CLUSTERS.values()), centroids)

    # Эталонные отзывы: по 20 штук вокруг каждого центроида.
    ref_vectors = np.vstack([c + 0.8 * rng.normal(size=(20, DIM)) for c in centroids])
    ref_labels = np.repeat(np.asarray(ids, dtype=np.int64), 20)
    reference = ReferenceSet(ref_vectors.astype(np.float32), ref_labels)

    # Батч новых отзывов: по одному на кластер и один не похожий ни на что.
    batch = np.vstack([c + 0.8 * rng.normal(size=DIM) for c in centroids] + [rng.normal(size=DIM)])
    titles = [
        "«Приложение вылетает при входе»",
        "«Одобрили ипотеку, но ставку подняли»",
        "«Кешбэк за месяц так и не пришёл»",
        "«Спасибо, всё хорошо» (нет явной темы)",
    ]
    return catalog, reference, batch.astype(np.float32), titles


def print_result(titles: list[str], result: list[ClusterAssignment]) -> None:
    print(f"\nСтратегия: {result[0].strategy}")
    for title, a in zip(titles, result):
        cluster = "выброс → новая тема?" if a.is_outlier else f"{a.cluster_id} {a.cluster_name}"
        print(f"  {title:42} → {cluster:28} score={a.score:.3f}")


def main() -> None:
    catalog, reference, batch, titles = make_data(np.random.default_rng(42))

    registry = StrategyRegistry()
    registry.register("cosine_centroid", lambda: CosineCentroidStrategy(catalog))
    registry.register("knn_voting", lambda: KnnVotingStrategy(reference, k=7))
    registry.register("faiss_centroid", lambda: FaissCentroidStrategy(catalog))

    assigner = ClusterAssigner(registry.create("cosine_centroid"), catalog, min_similarity=0.5)
    print_result(titles, assigner.assign(batch))

    # Подмена алгоритма на ходу: контекст и вызывающий код не меняются.
    assigner.set_strategy(registry.create("knn_voting"))
    print_result(titles, assigner.assign(batch))

    try:
        assigner.set_strategy(registry.create("faiss_centroid"))
        print_result(titles, assigner.assign(batch))
    except RuntimeError as exc:
        print(f"\nСтратегия faiss_centroid пропущена: {exc}")


if __name__ == "__main__":
    main()
