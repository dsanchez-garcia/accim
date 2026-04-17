__version__ = "0.7.8"

import sys
if sys.version_info >= (3, 12):
    if "imp" not in sys.modules:
        import types
        sys.modules["imp"] = types.ModuleType("imp")

# Monkey-patch: register a dask tokenizer for besos.evaluator.EvaluatorEP.
# Newer dask versions (>=2024) require deterministic tokenization of any
# callable passed to ddf.apply(). EvaluatorEP contains non-serializable
# state (IDF building objects) that cannot be pickled, causing a
# TokenizationError. Using id() provides a stable, per-instance token
# valid for the lifetime of a single Python process.
try:
    from besos.evaluator import EvaluatorEP
    from dask.tokenize import normalize_token

    @normalize_token.register(EvaluatorEP)
    def _tokenize_evaluator_ep(obj):
        return str(id(obj))

except (ImportError, AttributeError):
    pass