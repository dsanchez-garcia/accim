import pandas as pd

from accim.parametric_and_optimisation import preflight_report
from accim.parametric_and_optimisation.main import ParametricSimulation


class _DummyProblem:
    def __init__(self, inputs, outputs):
        self._inputs = inputs
        self._outputs = outputs

    def names(self, typ):
        if typ == 'inputs':
            return self._inputs
        if typ == 'outputs':
            return self._outputs
        if typ == 'constraints':
            return []
        raise KeyError(typ)


def _make_lightweight_parametric(epws, inputs):
    sim = ParametricSimulation(
        buildings=None,
        epws=epws,
        parameters_type=None,
        bypass_addAccis=True,
    )
    sim.problem = _DummyProblem(inputs=inputs, outputs=['energy'])
    return sim


def test_preflight_report_estimates_tasks_and_recommends_safe_defaults(monkeypatch):
    monkeypatch.setattr(
        ParametricSimulation,
        '_get_system_resource_snapshot',
        staticmethod(lambda: {'logical_cpus': 12, 'total_ram_gb': 16.0, 'available_ram_gb': 2.2}),
    )

    sim = _make_lightweight_parametric(epws=['A.epw', 'B.epw'], inputs=['x'])
    sim.parameters_values_df = pd.DataFrame({'x': [1, 2, 3]})

    report = sim.preflight_report_parametric(verbose=False, target_batches=60)

    assert report['status'] == 'ok'
    assert report['rows_in_df'] == 3
    assert report['estimated_total_tasks'] == 6
    assert report['recommendation']['processes'] == 1
    assert report['recommendation']['batch_size'] == 10


def test_preflight_report_detects_missing_required_columns():
    sim = _make_lightweight_parametric(epws=['A.epw'], inputs=['x', 'y'])
    sim.parameters_values_df = pd.DataFrame({'x': [1, 2, 3]})

    report = sim.preflight_report_parametric(verbose=False)

    assert report['status'] == 'check'
    assert report['missing_required_columns'] == ['y']
    assert report['estimated_total_tasks'] is None


def test_preflight_report_detects_unknown_epws():
    sim = _make_lightweight_parametric(epws=['A.epw'], inputs=['x'])
    sim.parameters_values_df = pd.DataFrame({'x': [1], 'epw': ['B.epw']})

    report = sim.preflight_report_parametric(verbose=False)

    assert report['status'] == 'check'
    assert report['unknown_epws_in_plan'] == ['B.epw']
    assert report['prepare_error'] is not None


def test_preflight_report_wrapper_uses_simulation_method():
    sim = _make_lightweight_parametric(epws=['A.epw'], inputs=['x'])
    sim.parameters_values_df = pd.DataFrame({'x': [1, 2]})

    report = preflight_report(sim, verbose=False)

    assert isinstance(report, dict)
    assert report['rows_in_df'] == 2
    assert 'recommendation' in report

