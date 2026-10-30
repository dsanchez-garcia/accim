# Tests for the core modules of accim
"""
Test suite for the modules outside accim.parametric_and_optimisation:
accim.sim (AddAccis, aPMV setpoints, the Erl interpreter and the Python API backend), accim.run,
accim.data and accim.utils. Most of them do not run EnergyPlus; those that do are skipped when the
EnergyPlus version they need is not installed.
"""
