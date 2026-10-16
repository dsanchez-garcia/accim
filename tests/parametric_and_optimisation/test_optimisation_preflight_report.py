import pandas as pd

from accim.parametric_and_optimisation import preflight_report
from accim.parametric_and_optimisation.main import OptimisationSimulation


class _DummyBuilding:
    def __init__(self, idfname: str):
        self.idfname = idfname
        self.idfobjects = {}

    def savecopy(self, backup_path: str):
        with open(backup_path, 'w', encoding='utf-8') as handle:
            handle.write('Version,9.6;\n')


class _DummyProblem:
    def __init__(self):
        self.minimize_outputs = [True]
        self.add_outputs = []

    def names(self, typ):
        if typ == 'inputs':
            return ['x']
        if typ == 'outputs':
            return ['obj']
        if typ == 'constraints':
            return []
        raise KeyError(typ)


def _make_lightweight_optimisation(epws):
    sim = OptimisationSimulation(
        buildings=None,
        epws=epws,
        parameters_type=None,
        bypass_addAccis=True,
    )
    sim.buildings = [_DummyBuilding('idf_a.idf'), _DummyBuilding('idf_b.idf')]
    sim.building = sim.buildings[0]
    sim.problem = _DummyProblem()
    return sim


def test_preflight_report_optimisation_estimates_cases_and_simulations(monkeypatch):
    monkeypatch.setattr(
        OptimisationSimulation,
        '_get_system_resource_snapshot',
        staticmethod(lambda: {'logical_cpus': 12, 'total_ram_gb': 16.0, 'available_ram_gb': 3.5}),
    )

    sim = _make_lightweight_optimisation(epws=['A.epw', 'B.epw'])

    report = sim.preflight_report_optimisation(
        evaluations=41,
        population_size=20,
        keep_sim_files='all',
        verbose=False,
    )

    assert report['run_type'] == 'optimisation'
    assert report['status'] == 'ok'
    assert report['estimated_cases'] == 4
    assert report['estimated_generations_per_case'] == 3
    assert report['estimated_simulations_per_case'] == 60
    assert report['estimated_total_simulations'] == 240
    assert report['recommendation']['processes'] == 1
    assert report['recommendation']['keep_sim_files'] == 'none'


def test_preflight_report_wrapper_auto_selects_optimisation(monkeypatch):
    monkeypatch.setattr(
        OptimisationSimulation,
        '_get_system_resource_snapshot',
        staticmethod(lambda: {'logical_cpus': 8, 'total_ram_gb': 32.0, 'available_ram_gb': 12.0}),
    )

    sim = _make_lightweight_optimisation(epws=['A.epw'])
    sim.outputs_optimisation = pd.DataFrame()

    report_auto = preflight_report(
        sim,
        evaluations=10,
        population_size=4,
        verbose=False,
    )
    report_explicit = preflight_report(
        sim,
        mode='optimisation',
        evaluations=10,
        population_size=4,
        verbose=False,
    )

    assert report_auto['run_type'] == 'optimisation'
    assert report_explicit['run_type'] == 'optimisation'
    assert report_auto['estimated_simulations_per_case'] == 12
    assert report_explicit['estimated_simulations_per_case'] == 12


def test_preflight_report_optimisation_counts_the_extra_offspring_of_odd_populations(monkeypatch):
    # NSGA-II creates offspring in pairs: with a population of 3, the second generation evaluates 4.
    monkeypatch.setattr(
        OptimisationSimulation,
        '_get_system_resource_snapshot',
        staticmethod(lambda: {'logical_cpus': 8, 'total_ram_gb': 32.0, 'available_ram_gb': 12.0}),
    )

    sim = _make_lightweight_optimisation(epws=['A.epw'])

    report = sim.preflight_report_optimisation(evaluations=6, population_size=3, verbose=False)

    assert report['estimated_cases'] == 2
    assert report['estimated_generations_per_case'] == 2
    assert report['estimated_simulations_per_case'] == 7
    assert report['estimated_total_simulations'] == 14

