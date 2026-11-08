# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Run the simulations of the IDFs and EPWs of the working folder (:func:`run_ep`), and estimate the size of their
results before running them (:func:`estimate_results_size`)."""

from accim.run.results_size import estimate_results_size
from accim.run.run import BACKENDS, remove_files, removefiles, runEp, run_ep

__all__ = ['BACKENDS', 'estimate_results_size', 'remove_files', 'removefiles', 'runEp', 'run_ep']
