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

# Monkey-patch: besos.optimizer.get_operator throws TypeError on platypus>=1.4.0
# because platypus.config.PlatypusConfig.default_variator was changed from a dict to a method.
try:
    import besos.optimizer
    import platypus
    # If default_variator is callable, we are on platypus >= 1.4.0
    if hasattr(platypus.config.PlatypusConfig.default_variator, '__call__'):
        def _get_operator_patched(problem: platypus.Problem, mutation=False):
            operators = []
            if mutation:
                class_ = platypus.CompoundMutation
                for t in problem.types:
                    operators.append(platypus.config.PlatypusConfig.default_mutator(t.__class__))
            else:
                class_ = platypus.CompoundOperator
                for t in problem.types:
                    operators.append(platypus.config.PlatypusConfig.default_variator(t.__class__))
            return class_(*operators)
            
        besos.optimizer.get_operator = _get_operator_patched
        
        # Re-wrap the standard platypus algorithms so they capture the patched get_operator
        _alg_names = [
            'GeneticAlgorithm', 'EvolutionaryStrategy', 'NSGAII', 'EpsMOEA',
            'GDE3', 'SPEA2', 'MOEAD', 'NSGAIII', 'ParticleSwarm', 'OMOPSO',
            'SMPSO', 'CMAES', 'IBEA', 'PAES', 'PESA2', 'EpsNSGAII'
        ]
        for _alg in _alg_names:
            if hasattr(platypus, _alg) and hasattr(besos.optimizer, _alg):
                setattr(besos.optimizer, _alg, besos.optimizer._alg_t(getattr(platypus, _alg)))

except (ImportError, AttributeError):
    pass

# Monkey-patch: besos.evaluator._freeze fails on platypus>=1.4.0
# because platypus.core.FixedLengthArray is not deemed Iterable by isinstance()
# but it is passed as a solution.variables instance that needs hashing for the cache.
try:
    import besos.evaluator
    _original_freeze = besos.evaluator._freeze
    def _freeze_patched(value):
        if type(value).__name__ == 'FixedLengthArray':
            return tuple(_freeze_patched(value[i]) for i in range(len(value)))
        return _original_freeze(value)
    
    besos.evaluator._freeze = _freeze_patched
except (ImportError, AttributeError):
    pass