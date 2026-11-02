# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""A graphical user interface (GUI) for accim, in English: add the ACCIS or the aPMV setpoints to IDF files, rename the
EPW files, run the simulations, measure the occupied hours within the setpoints, make tables and figures of the
results and run a basic parametric study, without writing Python.

Open it with the command ``accim-gui``, installed with accim, or with ``python -m accim.gui``. It uses tkinter, which
comes with Python on Windows and macOS (on Linux, it may need the package of the distribution, such as
``python3-tk``).

- :mod:`accim.gui.forms`: the fields of the forms and the arguments of accim that they give (without tkinter).
- :mod:`accim.gui.tasks`: the tasks of the tabs that run accim with these arguments (without tkinter).
- :mod:`accim.gui.app`: the window.
"""

__all__ = ['main']


def main() -> None:
    """Open the graphical user interface of accim."""
    from accim.gui.app import main as _main

    _main()
