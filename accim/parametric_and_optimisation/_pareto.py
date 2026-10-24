"""Shared constraint-aware dominance for result annotation and worker pruning."""

import numpy as np
from platypus import Constraint


def non_dominated_mask(problem, objectives, constraints=None):
    """Return the same constraint-first Pareto ordering as Platypus.

    Less total absolute constraint violation dominates more violation. Equal
    violations are compared on objectives, including when all rows are
    infeasible. Duplicate points remain non-dominated. Invalid/missing data
    raises before any cleanup; inputs are never modified.
    """
    names = list(problem.names('outputs'))
    constraint_names = list(problem.names('constraints'))
    bounds = list(getattr(problem, 'constraint_bounds', None) or [])
    if len(bounds) != len(constraint_names):
        raise ValueError('Constraint names and bounds must have the same length.')
    if not names:
        raise ValueError('Pareto dominance requires at least one objective.')
    try:
        costs = np.array(objectives, dtype=float, copy=True)
    except (TypeError, ValueError) as exc:
        raise ValueError('Pareto objectives must be finite numeric values.') from exc
    if costs.ndim != 2 or costs.shape[1] != len(names):
        raise ValueError('Objective data does not match the problem schema.')
    if not np.isfinite(costs).all():
        raise ValueError('Pareto objectives must contain only finite values.')
    directions = getattr(problem, 'minimize_outputs', None)
    directions = [True] * len(names) if directions is None else list(directions)
    if len(directions) != len(names):
        raise ValueError('Objective directions do not match the problem schema.')
    for column, minimize in enumerate(directions):
        # Matches Problem.to_platypus: false-valued directions are MAXIMIZE.
        if not minimize:
            costs[:, column] *= -1

    violations = np.zeros(len(costs))
    if constraint_names:
        try:
            values = np.asarray(constraints, dtype=float)
        except (TypeError, ValueError) as exc:
            raise ValueError('Constraint data must be finite numeric values.') from exc
        if values.shape != (len(costs), len(bounds)):
            raise ValueError('Missing constraint data or incompatible constraint schema.')
        if not np.isfinite(values).all():
            raise ValueError('Constraint data must contain only finite values.')
        checks = [Constraint.to_constraint(bound) for bound in bounds]
        for row, vector in enumerate(values):
            violations[row] = sum(abs(check(value)) for check, value in zip(checks, vector))
        if not np.isfinite(violations).all():
            raise ValueError('Constraint functions returned non-finite violation values.')

    if not len(costs):
        return np.zeros(0, dtype=bool)
    eligible = violations == violations.min()
    mask = eligible.copy()
    candidates = np.flatnonzero(eligible)
    candidate_costs = costs[candidates]
    for index in candidates:
        dominates = np.all(candidate_costs <= costs[index], axis=1) & np.any(
            candidate_costs < costs[index], axis=1
        )
        mask[index] = not np.any(dominates)
    return mask

