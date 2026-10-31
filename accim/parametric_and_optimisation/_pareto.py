# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Pareto status of the evaluations of an optimisation, with the constraints of its problem.

The evaluations are compared as Platypus compares the solutions of its algorithms (``ParetoDominance``): a smaller
total violation of the constraints dominates a larger one, so an evaluation that meets them dominates any that does
not, and the objectives only decide between evaluations with the same violation. Adapted from the branch
``review/refactor-sim-v1-20261024`` (``notes/branch-reviews.md``, section 1.3).
"""
import numpy as np

__all__ = ['constraint_violations', 'non_dominated_mask', 'valid_rows']


def _as_table(values, what: str) -> np.ndarray:
    try:
        table = np.array(values, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'The {what} must be numbers.') from exc
    if table.ndim == 1:
        table = table.reshape(-1, 1) if len(table) else table.reshape(0, 0)
    if table.ndim != 2:
        raise ValueError(f'The {what} must be a table: one row per evaluation, one column for each {what[:-1]}.')
    return table


def valid_rows(objectives, constraints=None) -> np.ndarray:
    """Whether each evaluation has finite values in all its objectives and constraints."""
    valid = np.isfinite(_as_table(objectives, 'objectives')).all(axis=1)
    if constraints is not None:
        values = _as_table(constraints, 'constraints')
        if values.size:
            valid &= np.isfinite(values).all(axis=1)
    return valid


def constraint_violations(problem, constraints) -> np.ndarray:
    """The total absolute violation of the constraints in each row of ``constraints`` (0 when the row meets them
    all), with the bounds of the problem (``constraint_bounds``, in the format of Platypus, such as '<=750')."""
    values = _as_table(constraints, 'constraints')
    bounds = list(getattr(problem, 'constraint_bounds', None) or [])
    if values.size == 0 and not bounds:
        return np.zeros(len(values))
    if values.shape[1] != len(bounds):
        raise ValueError(f'The problem has {len(bounds)} constraint bounds for {values.shape[1]} constraints.')
    from platypus import Constraint

    checks = [Constraint.to_constraint(bound) for bound in bounds]
    return np.array([sum(abs(check(value)) for check, value in zip(checks, row)) for row in values], dtype=float)


def non_dominated_mask(problem, objectives, constraints=None) -> np.ndarray:
    """Whether each evaluation is non-dominated (pareto-optimal), with the constraints of the problem.

    :param problem: The BESOS problem: its ``minimize_outputs`` (None means minimise) and ``constraint_bounds``.
    :param objectives: The values of the objectives, one row per evaluation, in the order of the outputs.
    :param constraints: The values of the constraints, in the order of the constraints of the problem (None if
        it has none).
    :return: A boolean array. The evaluations whose objectives or constraints are not finite numbers are never
        non-dominated, and they do not dominate the others. Identical evaluations are all non-dominated.
    """
    costs = _as_table(objectives, 'objectives').copy()
    valid = valid_rows(costs, constraints)
    minimize = getattr(problem, 'minimize_outputs', None)
    for column in range(costs.shape[1]):
        if minimize is not None and minimize[column] is not None and not minimize[column]:
            costs[:, column] *= -1
    mask = np.zeros(len(costs), dtype=bool)
    if not valid.any():
        return mask
    rows = np.flatnonzero(valid)
    violations = np.zeros(len(rows))
    if constraints is not None and _as_table(constraints, 'constraints').size:
        violations = constraint_violations(problem, _as_table(constraints, 'constraints')[rows])
    # Only the evaluations with the smallest violation can be non-dominated (all those that meet the constraints)
    candidates = rows[violations == violations.min()]
    candidate_costs = costs[candidates]
    for row in candidates:
        dominated = np.all(candidate_costs <= costs[row], axis=1) & np.any(candidate_costs < costs[row], axis=1)
        mask[row] = not dominated.any()
    return mask
