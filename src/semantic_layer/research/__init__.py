"""Research contracts and empirical evaluation exports.

The benchmark runner is imported lazily so lightweight contract consumers do
not create a reasoning-package cycle during module initialization.
"""

__all__ = ["BenchmarkRunner", "EvaluationReport"]


def __getattr__(name: str):
    if name in __all__:
        from semantic_layer.research.benchmark_runner import BenchmarkRunner, EvaluationReport

        return {"BenchmarkRunner": BenchmarkRunner, "EvaluationReport": EvaluationReport}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
