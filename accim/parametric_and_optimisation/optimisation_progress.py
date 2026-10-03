"""Progress reporting for ACCIM optimisation runs.

Platypus algorithms evaluate solutions in batches (one batch per generation for
generational algorithms such as NSGA-II) through ``evaluator.evaluate_all``.
This module wraps the active Platypus evaluator so that, from the main process,
ACCIM can report how many simulations have finished, the current generation,
the expected total and an approximate ETA.

The final number of simulations is not strictly known in advance; for
generational algorithms it is ``population_size * ceil(evaluations /
population_size)`` per IDF/EPW case, which is used as an estimate (prefixed
with ``~``). Steady-state algorithms may evaluate smaller batches.

Usage
-----
Used internally by ``SimulationBase.run_optimisation``.

Examples
--------
reporter = OptimisationProgressReporter(total_cases=2, sims_per_case=30, total_expected_sims=60, processes=4)
evaluator = ProgressReportingEvaluator(inner=platypus.MapEvaluator(), reporter=reporter)
"""

import time
import concurrent.futures

try:  # pragma: no cover - depends on installed platypus version
    from platypus.evaluator import Evaluator as _PlatypusEvaluatorBase
except Exception:  # pragma: no cover
    _PlatypusEvaluatorBase = object


def _run_platypus_job(job):
    """Run a Platypus job and return it (picklable worker function).

    Parameters
    ----------
    job : Any
        Platypus job exposing ``run()``.

    Returns
    -------
    Any
        The same job, after evaluation.

    Examples
    --------
    job = _run_platypus_job(job)
    """
    job.run()
    return job


def _format_seconds(seconds: float) -> str:
    """Format a duration in seconds as ``H:MM:SS``.

    Parameters
    ----------
    seconds : float
        Duration in seconds.

    Returns
    -------
    str
        Formatted duration.

    Examples
    --------
    _format_seconds(3725)  # '1:02:05'
    """
    seconds = max(0, int(round(seconds)))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f'{hours}:{minutes:02d}:{secs:02d}'


class OptimisationProgressReporter:
    """Keep track of optimisation progress and print status lines.

    Parameters
    ----------
    total_cases : int
        Total number of IDF/EPW cases in the run (including resumed ones).
    sims_per_case : int
        Estimated number of simulations per case.
    total_expected_sims : int
        Estimated number of simulations to run (excluding resumed cases).
    processes : int
        Number of parallel processes used.
    prefix : str
        Prefix for printed lines.

    Examples
    --------
    reporter = OptimisationProgressReporter(total_cases=1, sims_per_case=10, total_expected_sims=10, processes=1)
    """

    def __init__(self, total_cases: int, sims_per_case: int, total_expected_sims: int,
                 processes: int = 1, prefix: str = '[run_optimisation]'):
        self.total_cases = int(total_cases)
        self.sims_per_case = int(sims_per_case)
        self.total_expected_sims = int(total_expected_sims)
        self.processes = int(processes)
        self.prefix = prefix
        self.run_start = time.time()
        self.total_done = 0
        self.case_idx = 0
        self.case_label = ''
        self.case_done = 0
        self.case_start = None
        self.generation = 0

    def _print(self, msg: str):
        print(f'{self.prefix} {msg}', flush=True)

    def start_run(self, algorithm: str, evaluations: int, population_size: int, resumed_cases: int = 0):
        """Print the run header with the estimated number of simulations."""
        self.run_start = time.time()
        pending_cases = max(0, self.total_cases - int(resumed_cases))
        gens = self.sims_per_case // population_size if population_size else 0
        self._print(
            f'Starting optimisation ({algorithm}): {self.total_cases} case(s) '
            f'({pending_cases} to run, {resumed_cases} resumed) | '
            f'~{self.sims_per_case} sims/case ({gens} generation(s) x {population_size}, '
            f'evaluations={evaluations}) | ~{self.total_expected_sims} sims in total | '
            f'{self.processes} process(es)'
        )

    def start_case(self, case_idx: int, idf: str, epw: str):
        """Mark the beginning of a new IDF/EPW case."""
        self.case_idx = int(case_idx)
        self.case_label = f'idf={idf}, epw={epw}'
        self.case_done = 0
        self.generation = 0
        self.case_start = time.time()
        self._print(
            f'Case {self.case_idx}/{self.total_cases} started ({self.case_label}); '
            f'~{self.sims_per_case} simulation(s) expected.'
        )

    def skip_case(self, case_idx: int, idf: str, epw: str):
        """Report a case reused from checkpoint."""
        self._print(f'Case {int(case_idx)}/{self.total_cases} reused from checkpoint (idf={idf}, epw={epw}).')

    def end_case(self):
        """Report the end of the current case."""
        elapsed = time.time() - (self.case_start or time.time())
        self._print(
            f'Case {self.case_idx}/{self.total_cases} completed ({self.case_label}): '
            f'{self.case_done} simulation(s), {self.generation} generation(s) in {_format_seconds(elapsed)}.'
        )

    def start_generation(self, n_jobs: int):
        """Report the beginning of a new evaluation batch (generation)."""
        self.generation += 1
        self._print(
            f'Case {self.case_idx}/{self.total_cases} | generation {self.generation}: '
            f'evaluating {n_jobs} individual(s)...'
        )

    def job_done(self, gen_done: int, gen_total: int):
        """Report one completed simulation."""
        self.case_done += 1
        self.total_done += 1
        elapsed = time.time() - self.run_start
        remaining = max(0, self.total_expected_sims - self.total_done)
        eta = (elapsed / self.total_done) * remaining if self.total_done else 0.0
        pct = 100.0 * self.total_done / self.total_expected_sims if self.total_expected_sims else 0.0
        self._print(
            f'Case {self.case_idx}/{self.total_cases} | gen {self.generation} sim {gen_done}/{gen_total} | '
            f'case {self.case_done}/~{self.sims_per_case} | '
            f'total {self.total_done}/~{self.total_expected_sims} ({pct:.1f}%) | '
            f'elapsed {_format_seconds(elapsed)} | ETA ~{_format_seconds(eta)}'
        )


class ProgressReportingEvaluator(_PlatypusEvaluatorBase):
    """Platypus evaluator wrapper that reports per-simulation progress.

    Parameters
    ----------
    inner : Any
        Wrapped Platypus evaluator (e.g. ``MapEvaluator`` or ``ProcessPoolEvaluator``).
    reporter : OptimisationProgressReporter
        Reporter receiving progress events.

    Examples
    --------
    PlatypusConfig.default_evaluator = ProgressReportingEvaluator(inner, reporter)
    """

    def __init__(self, inner, reporter: OptimisationProgressReporter):
        self._inner = inner
        self._reporter = reporter

    def __getattr__(self, name):
        return getattr(self.__dict__['_inner'], name)

    def evaluate_all(self, jobs, **kwargs):
        """Evaluate jobs preserving order while reporting each completion."""
        jobs = list(jobs)
        n_jobs = len(jobs)
        if n_jobs == 0:
            return []
        self._reporter.start_generation(n_jobs)

        submit_func = getattr(self._inner, 'submit_func', None)
        map_func = getattr(self._inner, 'map_func', None)

        if callable(submit_func):
            futures = [submit_func(_run_platypus_job, job) for job in jobs]
            if all(isinstance(f, concurrent.futures.Future) for f in futures):
                for i, future in enumerate(concurrent.futures.as_completed(futures), start=1):
                    future.result()
                    self._reporter.job_done(i, n_jobs)
                return [f.result() for f in futures]
            results = []
            for i, future in enumerate(futures, start=1):
                results.append(future.result())
                self._reporter.job_done(i, n_jobs)
            return results

        if map_func is None or map_func is map:
            results = []
            for i, job in enumerate(jobs, start=1):
                results.append(_run_platypus_job(job))
                self._reporter.job_done(i, n_jobs)
            return results

        # Unknown evaluator: delegate and report the whole batch at once.
        results = list(self._inner.evaluate_all(jobs, **kwargs))
        for i in range(1, n_jobs + 1):
            self._reporter.job_done(i, n_jobs)
        return results

    def close(self):
        """Close the wrapped evaluator when supported."""
        close = getattr(self._inner, 'close', None)
        if callable(close):
            close()

