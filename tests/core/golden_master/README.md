# Golden master of the output IDFs

`tests/core/test_golden_master.py` checks that the output IDFs of accim do not change by accident: it runs 31
configurations and compares their outputs, object by object and in their order, with the outputs stored in
`golden/`, those of accim 1.1.0. 29 of them are the configurations with which accim 1.0.0 was checked against accim
0.8.2 (the migration guide, section 9.3, lists the differences); `b21` and `b22` came later, with the arguments of the
existing HVAC systems (`existing_hvac_*`). Since accim 1.1.0, `AddAccis` reads the models with eppy instead of besos,
and eppy writes some numbers of the input models in another way (`2.0` as `2`, `0.00000001` as `1e-08`), with the
same values: the golden files of the 19 `AddAccis` configurations whose numbers changed were written again then,
after checking that only these numbers changed and that EnergyPlus gives the same results (`b02`, `b11` and `b17`).
In accim 1.2.0, the models of the in-memory functions with the EMS code of all the comfort standards (`s01` to `s06`
and `s09`) got that of the new comfort standard JPN Aqilah 2025 (23, at the end of the chains): their golden files
were written again after checking that only its code was added (the output IDFs of `AddAccis`, which only have the
code of the comfort standards of their zones, did not change). Also in accim 1.2.0 (the decisions of 2026-11-12),
comfort standards 9 and 10, IND IMAC R 7DRM and 30DRM, read the running means of their comfort models: the golden files
of 21 configurations were written again after checking, line by line, that only this changed: the output IDFs of 9
(with the EMS code of its outdoor metric, the mean of the 7 previous days) and of 10 (PMOT instead of RMOT) in `b01`
(16 of 200 files) and `b03`, one line of the program `SetVST` of every model in mixed mode (its branch of INT EN16798
no longer names comfort standard 10: `b02`, `b03`, `b05`, `b07` to `b10`, `b12`, `b13`, `b15` to `b17` and `b22`), and
the models with the code of all the comfort standards (`s01` to `s06` and `s09`).

| File | What it holds |
| --- | --- |
| `configs.py` | The configurations: 22 of `AddAccis` (`b01` to `b22`: all the script types, every comfort standard, category and comfort mode, PMV control, the existing HVAC systems (with the thermostats of the model in `b21`, and always available, with wider outdoor temperature limits and with backup ideal loads air systems in `b22`), OpenStudio models, EnergyPlus 25.1 and 26.2, `People:Instance`, `output_take_dataframe`, tolerance ranges...) and 9 of the in-memory functions (`s01` to `s09`: `add_accis_to_idf`, `modify_accis`, `gen_outputs_df` and the aPMV setpoints). With accim 0.8.2, `b10` gives no output IDF (its HVAC system has two kinds of heating coils). |
| `runner.py` | Runs a configuration and writes the canonical text of its outputs; also a command-line tool (below). |
| `inputs/` | The input models, compressed (`.idf.xz`): sample IDFs of `accim/sample_files/sample IDFs/input_IDFs`, updated to EnergyPlus 25.1 or 26.2 with `accim.utils.update_idf_version` (see `configs.INPUT_MODELS`); `vrf2zones262inst` has a `People:Definition` and a `People:Instance` object instead of each `People` object. |
| `golden/` | The canonical outputs of accim 1.1.0, one `.txt.xz` file for each configuration (about 0.4 MB in all). |

The canonical text of a configuration has each output file under a line `### <file name>`; the objects of an IDF
keep their order, with one field per line, without the comments and the spaces of the file.

## Running the test

```bash
python -m pytest tests/core/test_golden_master.py -q -p no:cacheprovider
```

It is part of `tests/core` and takes about a minute and a half. It needs EnergyPlus 25.1 and 26.2 (their IDD
files): the configurations whose version is not installed are skipped. Each configuration runs in its own Python
process (`runner.py write`, four at a time), because eppy reads all the models of a process with the IDD of the
first one. A failing configuration shows the difference from its first different line (4000 lines at most, so that
the diff of the biggest outputs takes seconds) and the path of its whole output.

## After an intended change of the output IDFs

1. See what changed: write the outputs of the working tree and compare them with the golden files.

   ```bash
   python tests/core/golden_master/runner.py write OUT_DIR
   python tests/core/golden_master/runner.py compare OUT_DIR
   ```

   (Run it from the root of the repository with `PYTHONPATH` set to it, if another accim is installed.)
2. Write the golden files again, and commit them with the change:

   ```bash
   python -m pytest tests/core/test_golden_master.py -q -p no:cacheprovider --update-golden
   ```

## Comparing with another version of accim

`runner.py write` uses the accim that Python imports first, so `PYTHONPATH` chooses the version, for instance a
git worktree of another commit. With `--legacy`, it calls the functions of accim 0.x (`addAccis`,
`accis_single_idf_funcs`, `apmv_setpoints`) with the names of their arguments; `compare --ignore-order` compares
the objects of each IDF in any order, as accim 0.x did not always write them in the same order. With accim 0.8.2
(the last commit of `master` before 1.0.0):

```bash
git worktree add --detach ../accim_0.8.2 master
PYTHONPATH=../accim_0.8.2 python tests/core/golden_master/runner.py write OUT_082 --legacy
python tests/core/golden_master/runner.py compare OUT_082 --ignore-order
git worktree remove ../accim_0.8.2
```

(In PowerShell, set `$env:PYTHONPATH = '..\accim_0.8.2'` first.) With accim 0.8.2, `s04` stops with a `NameError`
of accim 0.8.2, and the other configurations differ only in the corrections of the migration guide (section 9.3):
the output IDFs that accim 1.0.0 no longer writes (combinations without setpoints, natural ventilation with the
ventilation controls 2 and 3), the subprograms of ESP CTE and INT ISO7730, the unused coefficients of ESP CTE, the
averages of the occupied zones only, the calling managers of the programs of the input model, the sizing
calculations of the in-memory functions and the removed ideal loads systems. Since the operative temperature
control of the existing HVAC systems, the configurations with the OSM office and `ex_ac` or `ex_mm` (`b10`, `b11`,
`s04` and `b22`) also differ in its thermostats, which accim 0.x left controlling the air temperature. With
`--legacy`, the arguments of the existing HVAC systems (`existing_hvac_*`), which accim 0.x does not have, are left
out: `b21` is then the same configuration as `b11`, and its output with accim 0.x differs from its golden file only as
that of `b11` did before the operative temperature control. Since accim 1.1.0, the outputs of `AddAccis` of
accim 0.8.2 and 1.0.0 also differ in the numbers that eppy writes in another way (see above).
