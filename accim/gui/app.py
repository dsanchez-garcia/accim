# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The graphical user interface of accim, with tkinter: add the ACCIS to IDF files, run the simulations and measure
the occupied hours within the setpoints.

Open it with ``accim-gui`` (a command installed with accim) or ``python -m accim.gui``. Each task runs in a thread,
one at a time, in the folder of its tab, and what it prints appears in the log at the bottom of the window. The
values of the forms are checked by :mod:`accim.gui.forms`.
"""

import builtins
import contextlib
import os
import queue
import sys
import threading
import tkinter as tk
import traceback
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from typing import Any, Callable, Dict, List, Optional

from accim import __version__
from accim.gui import forms

__all__ = ['AccimApp', 'main']

DOCS_URL = 'https://accim.readthedocs.io/'


class _QueueWriter:
    """A text stream that puts what is written into a queue (the output of a task, for the log)."""

    def __init__(self, messages: queue.Queue):
        self.messages = messages

    def write(self, text: str) -> int:
        if text:
            self.messages.put(('text', text))
        return len(text)

    def flush(self) -> None:
        pass


@contextlib.contextmanager
def _no_prompts():
    """The interface cannot answer the questions of the prompt: ``input()`` raises an error instead of waiting."""
    original = builtins.input

    def refuse(prompt: str = '') -> str:
        raise RuntimeError(f'accim asked in the prompt {str(prompt).strip()!r}, which the graphical interface '
                           f'cannot answer: check the values of the form.')

    builtins.input = refuse
    try:
        yield
    finally:
        builtins.input = original


class _ScrollableFrame(ttk.Frame):
    """A frame whose content (``self.content``) scrolls vertically."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.content = ttk.Frame(self.canvas, padding=8)
        self.content.bind('<Configure>', lambda event: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        window = self.canvas.create_window((0, 0), window=self.content, anchor='nw')
        self.canvas.bind('<Configure>', lambda event: self.canvas.itemconfigure(window, width=event.width))
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        # The mouse wheel scrolls the frame while the pointer is over it
        self.content.bind('<Enter>', lambda event: self.canvas.bind_all('<MouseWheel>', self._wheel))
        self.content.bind('<Leave>', lambda event: self.canvas.unbind_all('<MouseWheel>'))

    def _wheel(self, event) -> None:
        self.canvas.yview_scroll(int(-event.delta / 120), 'units')


class _Tab:
    """A tab of the notebook; the folder is that of the whole window."""

    def __init__(self, app: 'AccimApp', title: str, scrollable: bool = False):
        self.app = app
        if scrollable:
            self.frame = _ScrollableFrame(app.notebook)
            self.body = self.frame.content
        else:
            self.frame = ttk.Frame(app.notebook, padding=8)
            self.body = self.frame
        app.notebook.add(self.frame, text=title)
        self.folder = app.folder

    def _folder_row(self, row: int, label: str, refresh: bool = False) -> None:
        line = ttk.Frame(self.body)
        line.grid(row=row, column=0, columnspan=2, sticky='ew', pady=(0, 6))
        ttk.Label(line, text=label).pack(side='left')
        ttk.Entry(line, textvariable=self.folder).pack(side='left', fill='x', expand=True, padx=6)

        def browse():
            folder = filedialog.askdirectory(initialdir=self.folder.get() or os.getcwd(), parent=self.app.root)
            if folder:
                self.folder.set(folder)

        ttk.Button(line, text='Browse...', command=browse).pack(side='left')
        if refresh:
            ttk.Button(line, text='Refresh', command=self.app.folder_changed).pack(side='left', padx=(6, 0))


def _grid_entry(parent, row: int, label: str, variable: tk.Variable, width: int = 18, column: int = 0) -> ttk.Entry:
    ttk.Label(parent, text=label).grid(row=row, column=column, sticky='w', padx=(0, 6), pady=2)
    entry = ttk.Entry(parent, textvariable=variable, width=width)
    entry.grid(row=row, column=column + 1, sticky='ew', pady=2)
    return entry


def _grid_combo(parent, row: int, label: str, variable: tk.Variable, values, width: int = 24) -> ttk.Combobox:
    ttk.Label(parent, text=label).grid(row=row, column=0, sticky='w', padx=(0, 6), pady=2)
    combo = ttk.Combobox(parent, textvariable=variable, values=list(values), state='readonly', width=width)
    combo.grid(row=row, column=1, sticky='ew', pady=2)
    return combo


def _set_state(widgets, enabled: bool) -> None:
    for widget in widgets:
        if isinstance(widget, ttk.Combobox):
            widget.configure(state='readonly' if enabled else 'disabled')
        elif isinstance(widget, tk.Listbox):
            widget.configure(state='normal' if enabled else 'disabled')
        else:
            widget.state(['!disabled'] if enabled else ['disabled'])


class AddAccisTab(_Tab):
    """Add the ACCIS to the IDF files of a folder (:class:`accim.sim.accis.AddAccis`)."""

    def __init__(self, app: 'AccimApp'):
        super().__init__(app, '1. Add the ACCIS', scrollable=True)
        defaults = forms.ADD_ACCIS_DEFAULTS
        body = self.body
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        self.vars: Dict[str, tk.Variable] = {}
        for name in ('script_type', 'supply_air_temp_input_method', 'setpoint_type', 'energyplus_version', 'output_type',
                     'category', 'comfort_mode', 'cooling_season_start', 'cooling_season_end', 'ventilation_setpoint_offset', 'min_outdoor_temp_offset',
                     'max_wind_speed', 'opening_factor_max_temp_diff', 'opening_factor_min_temp_diff', 'min_opening_factor', 'setpoint_tolerance_start',
                     'setpoint_tolerance_end', 'setpoint_tolerance_step', 'name_suffix', *forms.CUSTOM_MODEL_FIELDS):
            self.vars[name] = tk.StringVar(value=defaults[name])
        for name in ('keep_existing_outputs', 'add_building_averages'):
            self.vars[name] = tk.BooleanVar(value=defaults[name])
        self.frequencies = {f: tk.BooleanVar(value=f in defaults['output_frequencies']) for f in forms.OUTPUT_FREQUENCIES}
        self.hvac_modes = {m: tk.BooleanVar(value=m in defaults['hvac_mode']) for m in forms.HVAC_MODES}
        self.vent_ctrls = {c: tk.BooleanVar(value=c in defaults['ventilation_control']) for c in forms.VENT_CTRLS}
        self.standards = forms.comfort_standard_choices()

        self._folder_row(0, 'Working folder (input IDFs):', refresh=True)
        self._idf_frame(body).grid(row=1, column=0, columnspan=2, sticky='ew', pady=4)
        self._model_frame(body).grid(row=2, column=0, sticky='nsew', padx=(0, 6), pady=4)
        self._comfort_frame(body).grid(row=2, column=1, sticky='nsew', pady=4)
        self._mixed_mode_frame(body).grid(row=3, column=0, sticky='nsew', padx=(0, 6), pady=4)
        self._custom_frame(body).grid(row=3, column=1, sticky='nsew', pady=4)
        self._tolerance_frame(body).grid(row=4, column=0, columnspan=2, sticky='ew', pady=4)
        buttons = ttk.Frame(body)
        buttons.grid(row=5, column=0, columnspan=2, sticky='ew', pady=(6, 0))
        ttk.Button(buttons, text='Preview', command=self.preview).pack(side='left')
        self.add_button = ttk.Button(buttons, text='Add the ACCIS', command=self.add)
        self.add_button.pack(side='left', padx=6)
        self.count = tk.StringVar(value='')
        ttk.Label(buttons, textvariable=self.count).pack(side='left', padx=6)
        self.vars['script_type'].trace_add('write', lambda *args: self.update_state())
        self.vars['setpoint_type'].trace_add('write', lambda *args: self.update_state())
        self.update_state()

    def _idf_frame(self, parent) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text='Input IDFs (the selected ones)', padding=6)
        frame.columnconfigure(0, weight=1)
        self.idf_list = tk.Listbox(frame, selectmode='extended', height=5, exportselection=False)
        self.idf_list.grid(row=0, column=0, rowspan=2, sticky='ew')
        ttk.Button(frame, text='All', command=lambda: self.idf_list.selection_set(0, 'end')).grid(
            row=0, column=1, padx=(6, 0), sticky='ew')
        ttk.Button(frame, text='None', command=lambda: self.idf_list.selection_clear(0, 'end')).grid(
            row=1, column=1, padx=(6, 0), sticky='ew')
        return frame

    def _model_frame(self, parent) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text='Model', padding=6)
        frame.columnconfigure(1, weight=1)
        _grid_combo(frame, 0, 'Script type:', self.vars['script_type'], forms.SCRIPT_TYPES)
        self.script_description = ttk.Label(frame, text='', wraplength=380, foreground='gray25')
        self.script_description.grid(row=1, column=0, columnspan=2, sticky='w', pady=(0, 4))
        self.supply_air = _grid_combo(frame, 2, 'Supply air temperature input:', self.vars['supply_air_temp_input_method'],
                                      forms.SUPPLY_AIR_TEMP_INPUT_METHODS)
        _grid_combo(frame, 3, 'Temperature control:', self.vars['setpoint_type'], forms.TEMP_CTRLS)
        _grid_combo(frame, 4, 'EnergyPlus version:', self.vars['energyplus_version'], forms.ENERGYPLUS_VERSIONS)
        _grid_combo(frame, 5, 'Outputs:', self.vars['output_type'], forms.OUTPUT_TYPES)
        ttk.Label(frame, text='Output frequencies:').grid(row=6, column=0, sticky='nw', pady=2)
        checks = ttk.Frame(frame)
        checks.grid(row=6, column=1, sticky='w')
        for column, (frequency, variable) in enumerate(self.frequencies.items()):
            ttk.Checkbutton(checks, text=frequency, variable=variable).grid(row=column // 3, column=column % 3,
                                                                           sticky='w', padx=(0, 6))
        ttk.Checkbutton(frame, text='Keep the outputs of the input IDFs',
                        variable=self.vars['keep_existing_outputs']).grid(row=7, column=0, columnspan=2, sticky='w')
        ttk.Checkbutton(frame, text='Building averages of the hour counters (add_building_averages)',
                        variable=self.vars['add_building_averages']).grid(row=8, column=0, columnspan=2, sticky='w')
        return frame

    def _comfort_frame(self, parent) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text='Comfort models (adaptive setpoints)', padding=6)
        frame.columnconfigure(1, weight=1)
        self.comfort_widgets: List[Any] = []
        ttk.Label(frame, text='Comfort standards (select one or more):').grid(row=0, column=0, columnspan=2,
                                                                             sticky='w', pady=2)
        lines = ttk.Frame(frame)
        lines.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 4))
        lines.columnconfigure(0, weight=1)
        self.standard_list = tk.Listbox(lines, selectmode='extended', height=7, exportselection=False)
        scrollbar = ttk.Scrollbar(lines, orient='vertical', command=self.standard_list.yview)
        self.standard_list.configure(yscrollcommand=scrollbar.set)
        self.standard_list.grid(row=0, column=0, sticky='ew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        for index, (number, title) in enumerate(self.standards):
            self.standard_list.insert('end', title)
            if number in forms.ADD_ACCIS_DEFAULTS['comfort_standard']:
                self.standard_list.selection_set(index)
        self.standard_list.bind('<<ListboxSelect>>', lambda event: self.update_state())
        self.comfort_widgets.append(self.standard_list)
        self.comfort_widgets.append(_grid_entry(frame, 2, 'Categories:', self.vars['category']))
        self.categories = ttk.Label(frame, text='', wraplength=380, foreground='gray25')
        self.categories.grid(row=3, column=0, columnspan=2, sticky='w')
        self.comfort_widgets.append(_grid_entry(frame, 4, 'Comfort modes:', self.vars['comfort_mode']))
        self.comfort_modes = ttk.Label(frame, text='', wraplength=380, foreground='gray25')
        self.comfort_modes.grid(row=5, column=0, columnspan=2, sticky='w')
        self.comfort_widgets.append(_grid_entry(frame, 6, 'Cooling season from (dd/mm or day):',
                                                self.vars['cooling_season_start']))
        self.comfort_widgets.append(_grid_entry(frame, 7, 'to (dd/mm or day):', self.vars['cooling_season_end']))
        return frame

    def _mixed_mode_frame(self, parent) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text='Mixed mode (script types vrf_mm and ex_mm)', padding=6)
        frame.columnconfigure(1, weight=1)
        self.mixed_mode_widgets: List[Any] = []
        ttk.Label(frame, text='HVAC modes:').grid(row=0, column=0, sticky='nw', pady=2)
        modes = ttk.Frame(frame)
        modes.grid(row=0, column=1, sticky='w')
        for row, (mode, label) in enumerate(forms.HVAC_MODES.items()):
            check = ttk.Checkbutton(modes, text=f'{mode}: {label}', variable=self.hvac_modes[mode])
            check.grid(row=row, column=0, sticky='w')
            self.mixed_mode_widgets.append(check)
        ttk.Label(frame, text='Ventilation controls\n(2 and 3: HVAC mode 2):').grid(row=1, column=0, sticky='nw',
                                                                                 pady=2)
        controls = ttk.Frame(frame)
        controls.grid(row=1, column=1, sticky='w')
        for row, (control, label) in enumerate(forms.VENT_CTRLS.items()):
            check = ttk.Checkbutton(controls, text=f'{control}: {label}', variable=self.vent_ctrls[control])
            check.grid(row=row, column=0, sticky='w')
            self.mixed_mode_widgets.append(check)
        for row, (name, label) in enumerate((
                ('ventilation_setpoint_offset', 'Offsets of the ventilation setpoint (°C):'),
                ('min_outdoor_temp_offset', 'Offsets of the minimum outdoor temperature (°C):'),
                ('max_wind_speed', 'Maximum wind speeds (m/s):'),
                ('opening_factor_max_temp_diff', 'Opening factor: maximum temperature difference:'),
                ('opening_factor_min_temp_diff', 'Opening factor: minimum temperature difference:'),
                ('min_opening_factor', 'Opening factor: multiplier (0 to 1):')), start=2):
            self.mixed_mode_widgets.append(_grid_entry(frame, row, label, self.vars[name]))
        return frame

    def _custom_frame(self, parent) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text='Custom comfort model (comfort standard 99)', padding=6)
        frame.columnconfigure(1, weight=1)
        self.custom_widgets = [_grid_entry(frame, row, f'{label}:', self.vars[name])
                               for row, (name, (label, _)) in enumerate(forms.CUSTOM_MODEL_FIELDS.items())]
        return frame

    def _tolerance_frame(self, parent) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text='Tolerance of the setpoints and names of the output IDFs', padding=6)
        _grid_entry(frame, 0, 'Tolerance from (°C):', self.vars['setpoint_tolerance_start'], width=8)
        _grid_entry(frame, 0, 'to:', self.vars['setpoint_tolerance_end'], width=8, column=2)
        _grid_entry(frame, 0, 'in steps of:', self.vars['setpoint_tolerance_step'], width=8, column=4)
        _grid_entry(frame, 0, 'Name suffix:', self.vars['name_suffix'], width=14, column=6)
        for column in (2, 4, 6):
            frame.columnconfigure(column, pad=12)
        return frame

    def selected_standards(self) -> List[int]:
        return [self.standards[index][0] for index in self.standard_list.curselection()]

    def refresh_idfs(self) -> None:
        """List the input IDFs of the folder, all selected."""
        self.idf_list.delete(0, 'end')
        for name in forms.input_idfs(self.folder.get()):
            self.idf_list.insert('end', name)
        self.idf_list.selection_set(0, 'end')

    def update_state(self) -> None:
        """Enable the fields that apply to the script type, the temperature control and the comfort standards."""
        script_type = self.vars['script_type'].get()
        self.script_description.configure(text=forms.SCRIPT_TYPES.get(script_type, ''))
        _set_state([self.supply_air], script_type.startswith('vrf'))
        _set_state(self.mixed_mode_widgets, script_type in forms.MIXED_MODE_SCRIPT_TYPES)
        temperature = self.vars['setpoint_type'].get() == 'temperature'
        _set_state(self.comfort_widgets, temperature)
        standards = self.selected_standards() if temperature else []
        _set_state(self.custom_widgets, 99 in standards)
        self.categories.configure(text=forms.categories_hint(standards))
        self.comfort_modes.configure(text=forms.comfort_modes_hint(standards))

    def form(self) -> Dict[str, Any]:
        """The values of the form, for :func:`accim.gui.forms.add_accis_arguments`."""
        values: Dict[str, Any] = {name: variable.get() for name, variable in self.vars.items()}
        values.update(
            folder=self.folder.get(),
            idfs=[self.idf_list.get(index) for index in self.idf_list.curselection()],
            output_frequencies=[f for f, variable in self.frequencies.items() if variable.get()],
            comfort_standard=self.selected_standards(),
            hvac_mode=[m for m, variable in self.hvac_modes.items() if variable.get()],
            ventilation_control=[c for c, variable in self.vent_ctrls.items() if variable.get()],
        )
        if values['setpoint_type'] == 'pmv' and not values['comfort_standard']:
            # The comfort models are not used with PMV control, but AddAccis needs them
            values['comfort_standard'] = forms.ADD_ACCIS_DEFAULTS['comfort_standard']
        return values

    def _arguments(self) -> Optional[Dict[str, Any]]:
        try:
            arguments = forms.add_accis_arguments(self.form())
            count = forms.output_idf_count(arguments)
        except (forms.FormError, ValueError) as error:
            self.app.show_error('Add the ACCIS', str(error))
            return None
        total = count * len(arguments['idfs'])
        self.count.set(f'{count} output IDFs for each of the {len(arguments["idfs"])} input IDFs: {total} in all')
        arguments['_total'] = total
        return arguments

    def preview(self) -> None:
        """Show the number of output IDFs that the form gives, and the arguments of AddAccis."""
        arguments = self._arguments()
        if arguments is None:
            return
        total = arguments.pop('_total')
        self.app.log_text(f'\nAddAccis in {self.folder.get()} would write {total} output IDFs, with:\n'
                          + ''.join(f'    {name} = {value!r}\n' for name, value in arguments.items()))

    def add(self) -> bool:
        """Add the ACCIS to the selected IDFs, in the folder (in a thread)."""
        arguments = self._arguments()
        if arguments is None:
            return False
        total = arguments.pop('_total')
        if total == 0:
            self.app.show_error('Add the ACCIS', 'These arguments give no output IDF: check the comfort standards, '
                                                 'categories and comfort modes.')
            return False
        if not self.app.ask_yes_no('Add the ACCIS', f'Write {total} output IDFs in {self.folder.get()}?'):
            return False

        def task():
            from accim.sim.accis import AddAccis

            return len(AddAccis(**arguments).output_idfs)

        def done(written):
            self.app.folder_changed()
            self.app.show_info('Add the ACCIS', f'{written} output IDFs have been written.')

        return self.app.run_task('Add the ACCIS', self.folder.get(), task, on_done=done)


class RunTab(_Tab):
    """Run the simulations of the IDFs and EPWs of a folder (:func:`accim.run.run_ep`)."""

    def __init__(self, app: 'AccimApp'):
        super().__init__(app, '2. Run the simulations')
        defaults = forms.RUN_DEFAULTS
        body = self.body
        body.columnconfigure(1, weight=1)
        self.vars: Dict[str, tk.Variable] = {
            'only_accim_idfs': tk.BooleanVar(value=defaults['only_accim_idfs']),
            'processes': tk.StringVar(value=defaults['processes']),
            'energyplus_version': tk.StringVar(value=defaults['energyplus_version']),
            'backend': tk.StringVar(value=defaults['backend']),
        }
        self._folder_row(0, 'Working folder (IDFs and EPWs):', refresh=True)
        self.run_only_accim_check = ttk.Checkbutton(body, text="Only the output IDFs of accim (with '[' in the name)",
                                                    variable=self.vars['only_accim_idfs'], command=self.preview)
        self.run_only_accim_check.grid(row=1, column=0, columnspan=2, sticky='w', pady=2)
        ttk.Label(body, text='Simulations at the same time:').grid(row=2, column=0, sticky='w', pady=2)
        ttk.Spinbox(body, from_=1, to=max(os.cpu_count() or 1, 1), textvariable=self.vars['processes'],
                    width=6).grid(row=2, column=1, sticky='w', pady=2)
        _grid_combo(body, 3, 'EnergyPlus version of the IDFs:', self.vars['energyplus_version'],
                    forms.ENERGYPLUS_VERSIONS, width=10).grid(sticky='w')
        _grid_combo(body, 4, 'Backend:', self.vars['backend'], forms.BACKENDS, width=10).grid(sticky='w')
        ttk.Label(body, text='ems: the Energy Management System of EnergyPlus; api: the Python API of EnergyPlus '
                             '(EnergyPlus 24.2 or later), with the same results.', foreground='gray25',
                  wraplength=700).grid(row=5, column=0, columnspan=2, sticky='w', pady=(0, 6))
        buttons = ttk.Frame(body)
        buttons.grid(row=6, column=0, columnspan=2, sticky='w', pady=6)
        ttk.Button(buttons, text='Preview', command=self.preview).pack(side='left')
        ttk.Button(buttons, text='Run the simulations', command=self.run).pack(side='left', padx=6)
        ttk.Button(buttons, text='Remove the simulation files', command=self.remove_files).pack(side='left')
        self.count = tk.StringVar(value='')
        ttk.Label(body, textvariable=self.count).grid(row=7, column=0, columnspan=2, sticky='w')
        ttk.Label(body, text='Each simulation is named "IDF name[EPW name"; its CSV files are written in the '
                             'folder. "Remove the simulation files" keeps the IDF, EPW, CSV and ESO files.',
                  foreground='gray25', wraplength=700).grid(row=8, column=0, columnspan=2, sticky='w', pady=(6, 0))

    def form(self) -> Dict[str, Any]:
        """The values of the form, for :func:`accim.gui.forms.run_ep_arguments`."""
        values: Dict[str, Any] = {name: variable.get() for name, variable in self.vars.items()}
        values['folder'] = self.folder.get()
        return values

    def preview(self) -> None:
        pairs = forms.simulations(self.folder.get(), self.vars['only_accim_idfs'].get())
        idfs = sorted({idf for idf, _ in pairs})
        epws = sorted({epw for _, epw in pairs})
        self.count.set(f'{len(idfs)} IDFs and {len(epws)} EPWs: {len(pairs)} simulations')

    def run(self) -> bool:
        """Run the simulations of the folder (in a thread)."""
        try:
            arguments = forms.run_ep_arguments(self.form())
        except forms.FormError as error:
            self.app.show_error('Run the simulations', str(error))
            return False
        pairs = forms.simulations(self.folder.get(), arguments['only_accim_idfs'])
        if not pairs:
            self.app.show_error('Run the simulations', 'The folder has no IDFs or no EPWs to simulate.')
            return False
        if not self.app.ask_yes_no('Run the simulations', f'Run {len(pairs)} simulations in {self.folder.get()}?'):
            return False

        def task():
            from accim.run import run_ep

            run_ep(**arguments)

        return self.app.run_task('Run the simulations', self.folder.get(), task)

    def remove_files(self) -> bool:
        if not self.app.ask_yes_no('Remove the simulation files',
                                   f'Remove the files of the simulations of {self.folder.get()}, except the IDF, '
                                   f'EPW, CSV and ESO files?'):
            return False

        def task():
            from accim.run import remove_files

            remove_files()

        return self.app.run_task('Remove the simulation files', self.folder.get(), task)


class HoursTab(_Tab):
    """The occupied hours within the setpoints of the simulations of a folder
    (:mod:`accim.data.postprocessing.setpoint_hours`)."""

    def __init__(self, app: 'AccimApp'):
        super().__init__(app, '3. Hours within the setpoints')
        body = self.body
        body.columnconfigure(1, weight=1)
        body.rowconfigure(4, weight=1)
        self.minimum = tk.StringVar(value='90')
        self.zones = tk.StringVar(value='building')
        self.summary = None
        self._folder_row(0, 'Working folder (CSV files of the simulations):')
        _grid_entry(body, 1, 'Minimum percentage of the occupied hours within the setpoints:', self.minimum,
                    width=8).grid(sticky='w')
        _grid_combo(body, 2, 'Reached by:', self.zones, ('building', 'all'), width=10).grid(sticky='w')
        buttons = ttk.Frame(body)
        buttons.grid(row=3, column=0, columnspan=2, sticky='w', pady=6)
        ttk.Button(buttons, text='Compute', command=self.compute).pack(side='left')
        self.export_button = ttk.Button(buttons, text='Export to CSV...', command=self.export, state='disabled')
        self.export_button.pack(side='left', padx=6)
        self.result = tk.StringVar(value='The occupied hours in which the operative temperature is within the '
                                         'setpoints, as a percentage of the occupied hours (from the EMS outputs of '
                                         'the hours of accim in the CSV files).')
        tree_frame = ttk.Frame(body)
        tree_frame.grid(row=4, column=0, columnspan=2, sticky='nsew')
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(tree_frame, show='headings')
        vertical = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        horizontal = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        vertical.grid(row=0, column=1, sticky='ns')
        horizontal.grid(row=1, column=0, sticky='ew')
        self.tree.tag_configure('below', foreground='firebrick')
        ttk.Label(body, textvariable=self.result, wraplength=800).grid(row=5, column=0, columnspan=2, sticky='w',
                                                                       pady=(6, 0))

    def compute(self) -> bool:
        """Compute the percentages of the CSV files of the folder (in a thread)."""
        try:
            minimum = forms.parse_number(self.minimum.get(), 'minimum percentage')
        except forms.FormError as error:
            self.app.show_error('Hours within the setpoints', str(error))
            return False

        def task():
            from accim.data.postprocessing.setpoint_hours import hours_within_setpoints

            return hours_within_setpoints('.')

        return self.app.run_task('Hours within the setpoints', self.folder.get(), task,
                                 on_done=lambda summary: self.show(summary, minimum))

    def show(self, summary, minimum: float) -> None:
        """Show the percentages of each simulation, and which ones reach the minimum."""
        from accim.data.postprocessing.setpoint_hours import filter_by_hours_within_setpoints

        try:
            kept = filter_by_hours_within_setpoints(summary, minimum, zones=self.zones.get())
        except ValueError as error:
            self.app.show_error('Hours within the setpoints', str(error))
            return
        summary = summary.copy()
        summary['Reaches the minimum'] = summary.index.isin(kept.index)
        columns = ['Source'] + [c for c in summary.columns if str(c).endswith('[%]')] + ['Reaches the minimum']
        self.summary = summary[columns]
        self.tree.delete(*self.tree.get_children())
        self.tree.configure(columns=columns)
        for column in columns:
            self.tree.heading(column, text=column)
            self.tree.column(column, width=420 if column == 'Source' else 160, stretch=column == 'Source')
        for _, row in self.summary.iterrows():
            values = [row[c] if c == 'Source' else ('yes' if row[c] else 'no') if c == 'Reaches the minimum'
                      else ('' if row[c] != row[c] else f'{row[c]:.1f}') for c in columns]
            self.tree.insert('', 'end', values=values, tags=() if row['Reaches the minimum'] else ('below',))
        self.result.set(f'{len(kept)} of the {len(summary)} simulations reach {minimum} % of the occupied hours '
                        f'within the setpoints ({self.zones.get()}).')
        self.export_button.state(['!disabled'])

    def export(self) -> None:
        if self.summary is None:
            return
        path = filedialog.asksaveasfilename(parent=self.app.root, defaultextension='.csv',
                                            initialdir=self.folder.get(), initialfile='hours_within_setpoints.csv',
                                            filetypes=[('CSV files', '*.csv')])
        if path:
            self.summary.to_csv(path, index=False)
            self.app.log_text(f'\nThe table has been saved in {path}\n')


class AccimApp:
    """The main window of the graphical user interface of accim.

    :param root: The tkinter window; a new one if None.
    :ivar add_accis: The tab that adds the ACCIS.
    :ivar run: The tab that runs the simulations.
    :ivar hours: The tab of the occupied hours within the setpoints.
    """

    def __init__(self, root: Optional[tk.Tk] = None):
        self.root = root if root is not None else tk.Tk()
        self.root.title(f'accim {__version__}: Adaptive-Comfort-Control-Implemented Model')
        self.root.geometry('1100x800')
        self.root.minsize(800, 600)
        self.messages: queue.Queue = queue.Queue()
        self.busy = False
        #: The working folder of the three tabs
        self.folder = tk.StringVar(value=os.getcwd())
        panes = ttk.PanedWindow(self.root, orient='vertical')
        panes.pack(fill='both', expand=True, padx=6, pady=6)
        self.notebook = ttk.Notebook(panes)
        panes.add(self.notebook, weight=3)
        self.add_accis = AddAccisTab(self)
        self.run = RunTab(self)
        self.hours = HoursTab(self)
        log_frame = ttk.LabelFrame(panes, text='Log', padding=4)
        panes.add(log_frame, weight=1)
        self.log = ScrolledText(log_frame, height=8, wrap='word', state='disabled', font=('Consolas', 9))
        self.log.pack(fill='both', expand=True)
        status = ttk.Frame(self.root)
        status.pack(fill='x', padx=6, pady=(0, 6))
        self.status = tk.StringVar(value='Ready.')
        ttk.Label(status, textvariable=self.status).pack(side='left')
        ttk.Label(status, text=f'Documentation: {DOCS_URL}', foreground='gray25').pack(side='right')
        self.progress = ttk.Progressbar(status, mode='indeterminate', length=160)
        self.folder.trace_add('write', lambda *args: self.folder_changed())
        self.folder_changed()
        self._after = self.root.after(100, self.poll)

    def folder_changed(self) -> None:
        """List the files of the working folder again (the input IDFs, and the simulations)."""
        self.add_accis.refresh_idfs()
        self.run.preview()

    # Dialogs (the tests replace them)
    def show_error(self, title: str, message: str) -> None:
        messagebox.showerror(title, message, parent=self.root)

    def show_info(self, title: str, message: str) -> None:
        messagebox.showinfo(title, message, parent=self.root)

    def ask_yes_no(self, title: str, message: str) -> bool:
        return messagebox.askyesno(title, message, parent=self.root)

    def log_text(self, text: str) -> None:
        self.log.configure(state='normal')
        self.log.insert('end', text)
        self.log.see('end')
        self.log.configure(state='disabled')

    def set_busy(self, busy: bool, status: str) -> None:
        self.busy = busy
        self.status.set(status)
        if busy:
            self.progress.pack(side='right', padx=12)
            self.progress.start(12)
        else:
            self.progress.stop()
            self.progress.pack_forget()

    def run_task(self, title: str, folder: str, function: Callable[[], Any],
                 on_done: Optional[Callable[[Any], None]] = None) -> bool:
        """Run a task in a thread, in a folder; its output goes to the log, and ``on_done(result)`` runs when it ends.

        :return: False if another task is running.
        """
        if self.busy:
            self.show_info(title, 'Wait until the current task finishes.')
            return False
        if not os.path.isdir(folder):
            self.show_error(title, f'The folder {folder!r} does not exist.')
            return False
        self.set_busy(True, f'{title}...')
        self.log_text(f'\n===== {title} ({folder}) =====\n')
        threading.Thread(target=self.execute, args=(title, folder, function, on_done), daemon=True).start()
        return True

    def execute(self, title: str, folder: str, function: Callable[[], Any],
                on_done: Optional[Callable[[Any], None]] = None) -> None:
        """Run a task in the current thread: in its folder, with what it prints, and its end, in the queue of
        messages, which :meth:`process_messages` shows."""
        writer = _QueueWriter(self.messages)
        cwd = os.getcwd()
        try:
            with contextlib.redirect_stdout(writer), contextlib.redirect_stderr(writer), _no_prompts():
                os.chdir(folder)
                result = function()
        except Exception as error:  # noqa: BLE001 (any error of the task is shown)
            self.messages.put(('error', title, error, traceback.format_exc()))
        else:
            self.messages.put(('done', title, result, on_done))
        finally:
            os.chdir(cwd)

    def process_messages(self) -> None:
        """Show the output of the task and its end (in the thread of tkinter)."""
        try:
            while True:
                message = self.messages.get_nowait()
                if message[0] == 'text':
                    self.log_text(message[1])
                elif message[0] == 'done':
                    _, title, result, on_done = message
                    self.set_busy(False, f'{title}: done.')
                    self.log_text(f'===== {title}: done =====\n')
                    if on_done is not None:
                        on_done(result)
                else:
                    _, title, error, details = message
                    self.set_busy(False, f'{title}: failed.')
                    self.log_text(details)
                    self.show_error(title, f'{title} failed:\n\n{error}')
        except queue.Empty:
            pass

    def poll(self) -> None:
        """Process the messages of the task every 100 ms."""
        self.process_messages()
        self._after = self.root.after(100, self.poll)

    def close(self) -> None:
        """Close the window."""
        self.root.after_cancel(self._after)
        self.root.destroy()


def _set_dpi_awareness() -> None:
    """Sharp text on the screens of Windows with scaling."""
    if sys.platform == 'win32':
        try:
            import ctypes

            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass


def main() -> None:
    """Open the graphical user interface of accim."""
    _set_dpi_awareness()
    app = AccimApp()
    app.root.protocol('WM_DELETE_WINDOW', app.close)
    app.root.mainloop()
