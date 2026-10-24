Checkpoint integrity and owned workspaces
=========================================

.. note::

   This page describes development changes after accim 0.8.2. Public runner
   names are unchanged, but unsafe legacy checkpoint reuse is intentionally
   rejected rather than silently trusted.

Safe resume
-----------

``run_parametric_simulation`` saves completed batches when
``checkpoint_every_batch=True``. ``run_optimisation`` saves completed IDF/EPW
cases when ``checkpoint_every_case=True``. With ``resume_from_checkpoint=True``
these methods use their normal checkpoint filename in ``out_dir``; a string
selects an explicit checkpoint path.

Before reusing results, ACCIM validates:

* The checkpoint format, required columns, row counts and task/case metadata.
* Batch file existence and SHA256 digests, or the embedded optimisation history.
* The saved sampling plan and the backing results for completed tasks.
* Evaluation identity: prepared IDF contents, EPW contents, resolved EnergyPlus
  executable/IDD/library and preprocessing tools, parameter descriptors and
  selectors, output readers and reducers, directions, constraints, additional
  outputs, execution/storage options, ACCIM code and relevant package versions.

The new formats are ``parametric_state_v3`` and ``optimisation_state_v2``.
Identity is intentionally conservative: a change to runtime code or relevant
configuration may require a fresh run even when its effect appears unrelated.

Parametric resume retains the complete planned order and repeated rows. Repeated
parameter/IDF/EPW combinations are evaluated once but still appear for every
corresponding row in the returned results. ``resume_plan_source='auto'`` and
``'checkpoint'`` reuse the exact saved plan; ``'provided'`` explicitly selects
the new plan. Plan selection cannot override an evaluation-identity mismatch.

Optimisation resume reuses **completed cases**, not an interrupted population,
generation or random-number-generator state. An interrupted case is rerun.

What to do when recovery is rejected
--------------------------------------

A corrupt, incomplete, unknown-format, legacy or incompatible checkpoint raises
``ValueError`` (internally ``CheckpointError``). ACCIM does not overwrite that
checkpoint or return a shortened result table as successful recovery.

* If a referenced batch was moved or removed, restore the original batch at its
  recorded location. Referenced batch paths are currently absolute.
* If an input, reader, constraint, engine or other dependency changed, use a
  **new output directory** and ``resume_from_checkpoint=False``.
* Keep old checkpoints and results for inspection. Legacy DataFrame/``state_v2``
  parametric checkpoints and old optimisation checkpoints cannot establish the
  evaluation identity and are not automatically migrated or trusted.
* The normal ``load_outputs_parametric`` and ``load_outputs_optimisation``
  methods still read previously exported result files; loading results is not
  execution resume.

A missing *default* checkpoint with ``resume_from_checkpoint=True`` produces a
warning and starts a fresh run. A missing *explicit* checkpoint path raises
``FileNotFoundError``. Set ``resume_from_checkpoint=False`` only when deliberately
starting afresh, not as an automatic fallback after any recovery error.

Only load trusted pickle files. Hashes detect accidental corruption/incompatible
reuse; they do not make pickle safe to deserialize or authenticate an untrusted
checkpoint. Changes to external inputs during a running campaign are unsupported.

Custom external dependencies
----------------------------

Both runners accept the optional ``checkpoint_context`` dictionary. Use it to
declare dependencies that a custom selector, reducer or algorithm reads outside
the IDF/problem, such as a dataset revision or external calibration files.
``pathlib.Path`` values are hashed by file contents; plain strings are literal
revision identifiers, not implicit filesystem references.

Function code, defaults, closures, partial arguments and supported callable
object state are included in identity. This cannot infer arbitrary remote
services, mutable state inside third-party modules or all dynamically loaded
code. Declare those dependencies, keep them immutable during a run, or do not
reuse checkpoints. Unsupported opaque/cyclic identity values are rejected,
not compared by their memory-address representation. Notebook cell filenames
are excluded from function-code identity.

Common IDF external-file fields are checked. Models containing PythonPlugin
objects additionally require ``checkpoint_context`` declaring their code/data
dependencies. The dependency declaration is the caller's responsibility.

File ownership and concurrent runs
----------------------------------

Each parametric/optimisation invocation creates a unique ``accim_run_*``
workspace below ``out_dir``. Optimisation cases have their own directories below
it. Results continue to expose their actual ``output_dir`` or
``simulation_directory`` and ``simulation_output_csv_path`` values; applications
should use those columns rather than construct paths from ``BESOS_Output*``.

Automatic cleanup:

* Only prunes new simulation paths inside this invocation's workspace.
* Never removes prior/resumed directories or logs merely because their names
  match a prefix. A checkpoint grants no deletion authority over old files.
* Does not follow nested symbolic links or Windows junctions during extension
  cleanup.
* Removes its own workspace on successful ``keep_dirs=False`` or
  ``keep_sim_files='none'`` runs, after collecting results. Failed runs retain
  owned workspaces for diagnosis where artifacts exist.
* Keeps IDF backups outside the simulation workspace, with collision-resistant
  names and an exact identifier-to-backup mapping.

Operating-system advisory locks reject simultaneous writers to the same
``out_dir`` or checkpoint, including explicit checkpoint paths used from a
different results directory. Locks are released by the OS when a process exits.
Small ``.lock`` files remain deliberately; their existence does not mean a run
is active. Do not delete them while runs might be active. These locks coordinate
ACCIM writers on filesystems supporting OS locking; they are not a distributed
transaction or a guarantee of power-loss durability.

Output discovery uses unique ``available_outputs_*`` directories. With
``keep_available_outputs=True``, their actual paths are reported in the
returned ``meta`` dictionary (``paths`` for RDD/MDD and ``out_dirs`` for test
simulation discovery). The standalone ``print_available_outputs_mod`` helper
exposes ``out_dir``. Existing ``available_outputs`` RDD/MDD files can still be
read explicitly without simulation, but refresh never overwrites/deletes them.

The batch ``addAccis`` path likewise owns its working ``*_pymod.idf`` copies.
Version amendment is applied to the copy, leaving source IDF bytes unchanged.
A pre-existing same-name working copy causes ``FileExistsError`` rather than an
overwrite. Batch success, cancellation and failure clean only owned working
copies; ``genIDF(filelist_pymod=None)`` no longer scans unrelated working files.

Constraint-aware Pareto status
------------------------------

History annotation and worker pruning use one implementation of Platypus's
constraint-first dominance: lower total absolute violation dominates higher
violation; equal violations are compared by the configured objective directions.
When feasible points exist, infeasible points cannot displace them. When all
points are infeasible, the least-violating non-dominated candidates remain;
``pareto-optimal`` alone is therefore **not** a certificate of feasibility.

Missing or non-finite objective/constraint data raises before a dominance-based
cleanup decision. Duplicate points remain non-dominated and group boundaries
(``pareto_separate_by_epw`` / ``pareto_separate_by_idf``) remain effective.
A shared artifact path is not removed while a retained candidate references it.

Validation and remaining scope
------------------------------

Regression tests cover corrupt/missing batches, changed identities, interrupted
writes, legacy formats, ordering/duplicates, owned cleanup, source preservation,
OS locking and dominance against a Platypus oracle. The opt-in developer script
``benchmarks/checkpoint_integrity_smoke.py`` checks real serial/two-worker
parametric runs, additional outputs, constrained optimisation across two EPWs,
and resume without new simulations on an already prepared ACCIM model.

These changes do not replace CLI with the EnergyPlus Python API, unify the sim
engines or modify comfort formulas. Per-IDF output selection, other domain
correctness findings and the separately tracked unsafe IDF-expression reader
remain independent follow-up work.


