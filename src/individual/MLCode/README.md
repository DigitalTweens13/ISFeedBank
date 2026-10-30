# ЛР № 3 (ML): прототип компонента «Назначение кластера»

Компонент `cluster_assigner` воркера разметки (см. `../MLDiagramsCode/ml_l3.puml`) на паттерне «Стратегия».
Диаграмма классов: `../MLDiagramsCode/ml_l4.puml`, отчёт: `docs/reports/lab3/ML_Ershov_lab3_report.docx`.

Запуск из этой папки:

```
pip install -r requirements.txt   # faiss-cpu можно не ставить, тогда стратегия faiss_centroid пропускается
python demo.py                    # одна и та же обработка с тремя стратегиями
python -m unittest -v             # 8 тестов
mypy --strict cluster_assigner demo.py tests
```
