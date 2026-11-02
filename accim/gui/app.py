# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The graphical user interface of accim, with tkinter: add the ACCIS (with the arguments of each zone) or the aPMV
setpoints to IDF files, rename the EPW files, run the simulations, measure the occupied hours within the setpoints,
make tables and figures of the results with ``Table``, and run a basic parametric study.

Open it with ``accim-gui`` (a command installed with accim) or ``python -m accim.gui``. Each task runs in a thread,
one at a time, in the working folder, and what it prints appears in the log at the bottom of the window. The
values of the forms are checked by :mod:`accim.gui.forms`, and the tasks run by :mod:`accim.gui.tasks`.
"""

import builtins
import contextlib
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
import traceback
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from accim import __version__
from accim.gui import forms, tasks

__all__ = ['AccimApp', 'main']

DOCS_URL = 'https://accim.readthedocs.io/'
#: The number of rows of a table shown in the window (the exported files have all of them)
MAX_ROWS_SHOWN = 500


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
def _no_prompts(answers: Optional[Mapping[str, str]] = None):
    """The interface cannot answer the questions of the prompt: ``input()`` raises an error instead of waiting, except
    for the questions that begin with a key of ``answers``, which get its value (printed after the question, as if it
    was typed)."""
    original = builtins.input

    def refuse(prompt: str = '') -> str:
        question = str(prompt).strip()
        for beginning, answer in (answers or {}).items():
            if question.startswith(beginning):
                print(f'{prompt}{answer}')
                return answer
        raise RuntimeError(f'accim asked in the prompt {question!r}, which the graphical interface cannot answer: '
                           f'check the values of the form.')

    builtins.input = refuse
    try:
        yield
    finally:
        builtins.input = original


def _open_file(path: str) -> None:
    """Open a file with the default program of the system (a figure, for instance)."""
    try:
        if sys.platform == 'win32':
            os.startfile(path)  # noqa: S606 (a file written by the interface)
        else:
            subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', path])
    except (OSError, AttributeError):
        pass


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
        elif isinstance(widget, (tk.Listbox, tk.Text)):
            widget.configure(state='normal' if enabled else 'disabled')
        else:
            widget.state(['!disabled'] if enabled else ['disabled'])


def _list_frame(parent, text: str, height: int = 5) -> Tuple[ttk.LabelFrame, tk.Listbox]:
    """A frame with a list of several choices, and the buttons All and None."""
    frame = ttk.LabelFrame(parent, text=text, padding=6)
    frame.columnconfigure(0, weight=1)
    listbox = tk.Listbox(frame, selectmode='extended', height=height, exportselection=False)
    scrollbar = ttk.Scrollbar(frame, orient='vertical', command=listbox.yview)
    listbox.configure(yscrollcommand=scrollbar.set)
    listbox.grid(row=0, column=0, rowspan=2, sticky='nsew')
    scrollbar.grid(row=0, column=1, rowspan=2, sticky='ns')
    ttk.Button(frame, text='All', command=lambda: listbox.selection_set(0, 'end')).grid(
        row=0, column=2, padx=(6, 0), sticky='ew')
    ttk.Button(frame, text='None', command=lambda: listbox.selection_clear(0, 'end')).grid(
        row=1, column=2, padx=(6, 0), sticky='ew')
    return frame, listbox


def _fill_list(listbox: tk.Listbox, items, select_all: bool = True) -> None:
    listbox.delete(0, 'end')
    for item in items:
        listbox.insert('end', item)
    if select_all:
        listbox.selection_set(0, 'end')


def _selected(listbox: tk.Listbox) -> List[str]:
    return [listbox.get(index) for index in listbox.curselection()]


def _tree(parent, height: int = 10) -> ttk.Treeview:
    """A table with scroll bars, in a frame of its own (``tree.master``)."""
    frame = ttk.Frame(parent)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)
    tree = ttk.Treeview(frame, show='headings', height=height)
    vertical = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
    horizontal = ttk.Scrollbar(frame, orient='horizontal', command=tree.xview)
    tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
    tree.grid(row=0, column=0, sticky='nsew')
    vertical.grid(row=0, column=1, sticky='ns')
    horizontal.grid(row=1, column=0, sticky='ew')
    return tree


def _cell(value) -> str:
    if isinstance(value, float):
        return '' if value != value else f'{value:.4g}'
    return str(value)


def _show_dataframe(tree: ttk.Treeview, df, max_rows: int = MAX_ROWS_SHOWN) -> None:
    """Show the first rows of a DataFrame in a table of the window."""
    columns = [str(column) for column in df.columns]
    tree.delete(*tree.get_children())
    tree.configure(columns=columns)
    for column in columns:
        tree.heading(column, text=column)
        tree.column(column, width=max(90, min(300, 7 * len(column))), stretch=False)
    for row in df.head(max_rows).itertuples(index=False):
        tree.insert('', 'end', values=[_cell(value) for value in row])


def _export_dataframe(app: 'AccimApp', df, folder: str, name: str) -> None:
    """Save a DataFrame as a CSV or XLSX file chosen by the user."""
    path = filedialog.asksaveasfilename(parent=app.root, defaultextension='.csv', initialdir=folder,
                                        initialfile=name, filetypes=[('CSV files', '*.csv'), ('Excel files', '*.xlsx')])
    if not path:
        return
    if path.lower().endswith('.xlsx'):
        df.to_excel(path, index=False)
    else:
        df.to_csv(path, index=False)
    app.log_text(f'\nThe table has been saved in {path}\n')


class AddAccisTab(_Tab):
    """Add the ACCIS to the IDF files of a folder (:class:`accim.sim.accis.AddAccis`)."""

    def __init__(self, app: 'AccimApp'):
        super().__init__(app, '1. Add the ACCIS', scrollable=True)
        defaults = forms.ADD_ACCIS_DEFAULTS
        body = self.body
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        self.vars: Dict[str, tk.Variable] = {}
        for name in ('script_type', 'supply_air_temp_input_method', 'setpoint_type', 'energyplus_version',
                     'output_type', 'category', 'comfort_mode', 'cooling_season_start', 'cooling_season_end',
                     'ventilation_setpoint_offset', 'min_outdoor_temp_offset', 'max_wind_speed',
                     'opening_factor_max_temp_diff', 'opening_factor_min_temp_diff', 'min_opening_factor',
                     'setpoint_tolerance_start', 'setpoint_tolerance_end', 'setpoint_tolerance_step', 'name_suffix',
                     *forms.CUSTOM_MODEL_FIELDS):
            self.vars[name] = tk.StringVar(value=defaults[name])
        for name in ('keep_existing_outputs', 'add_building_averages'):
            self.vars[name] = tk.BooleanVar(value=defaults[name])
        self.frequencies = {f: tk.BooleanVar(value=f in defaults['output_frequencies'])
                            for f in forms.OUTPUT_FREQUENCIES}
        self.hvac_modes = {m: tk.BooleanVar(value=m in defaults['hvac_mode']) for m in forms.HVAC_MODES}
        self.ventilation_controls = {c: tk.BooleanVar(value=c in defaults['ventilation_control'])
                                     for c in forms.VENTILATION_CONTROLS}
        self.standards = forms.comfort_standard_choices()

        self._folder_row(0, 'Working folder (input IDFs):', refresh=True)
        self._idf_frame(body).grid(row=1, column=0, columnspan=2, sticky='ew', pady=4)
        self._model_frame(body).grid(row=2, column=0, sticky='nsew', padx=(0, 6), pady=4)
        self._comfort_frame(body).grid(row=2, column=1, sticky='nsew', pady=4)
        self._mixed_mode_frame(body).grid(row=3, column=0, sticky='nsew', padx=(0, 6), pady=4)
        self._custom_frame(body).grid(row=3, column=1, sticky='nsew', pady=4)
        self._tolerance_frame(body).grid(row=4, column=0, columnspan=2, sticky='ew', pady=4)
        self._zone_frame(body).grid(row=5, column=0, columnspan=2, sticky='ew', pady=4)
        buttons = ttk.Frame(body)
        buttons.grid(row=6, column=0, columnspan=2, sticky='ew', pady=(6, 0))
        ttk.Button(buttons, text='Preview', command=self.preview).pack(side='left')
        self.add_button = ttk.Button(buttons, text='Add the ACCIS', command=self.add)
        self.add_button.pack(side='left', padx=6)
        self.count = tk.StringVar(value='')
        ttk.Label(buttons, textvariable=self.count).pack(side='left', padx=6)
        self.vars['script_type'].trace_add('write', lambda *args: self.update_state())
        self.vars['setpoint_type'].trace_add('write', lambda *args: self.update_state())
        self.update_state()

    def _idf_frame(self, parent) -> ttk.LabelFrame:
        frame, self.idf_list = _list_frame(parent, 'Input IDFs (the selected ones)')
        return frame

    def _model_frame(self, parent) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text='Model', padding=6)
        frame.columnconfigure(1, weight=1)
        _grid_combo(frame, 0, 'Script type:', self.vars['script_type'], forms.SCRIPT_TYPES)
        self.script_description = ttk.Label(frame, text='', wraplength=380, foreground='gray25')
        self.script_description.grid(row=1, column=0, columnspan=2, sticky='w', pady=(0, 4))
        self.supply_air = _grid_combo(frame, 2, 'Supply air temperature input:',
                                      self.vars['supply_air_temp_input_method'], forms.SUPPLY_AIR_TEMP_INPUT_METHODS)
        _grid_combo(frame, 3, 'Setpoint type:', self.vars['setpoint_type'], forms.SETPOINT_TYPES)
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
        for row, (control, label) in enumerate(forms.VENTILATION_CONTROLS.items()):
            check = ttk.Checkbutton(controls, text=f'{control}: {label}', variable=self.ventilation_controls[control])
            check.grid(row=row, column=0, sticky='w')
            self.mixed_mode_widgets.append(check)
        for row, (name, label) in enumerate((
                ('ventilation_setpoint_offset', 'Offsets of the ventilation setpoint (°C):'),
                ('min_outdoor_temp_offset', 'Offsets of the minimum outdoor temperature (°C):'),
                ('max_wind_speed', 'Maximum wind speeds (m/s):'),
                ('opening_factor_max_temp_diff', 'Opening factor: maximum temperature difference:'),
                ('opening_factor_min_temp_diff', 'Opening factor: minimum temperature difference:'),
                ('min_opening_factor', 'Opening factor above the maximum difference (0 to 1):')), start=2):
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

    def _zone_frame(self, parent) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text='Arguments of some zones (zone_arguments): the other zones have those '
                                            'above', padding=6)
        frame.columnconfigure(1, weight=1)
        self.zone_tree = ttk.Treeview(frame, columns=('zone', 'arguments'), show='headings', height=4)
        self.zone_tree.heading('zone', text='Zone')
        self.zone_tree.heading('arguments', text='Arguments')
        self.zone_tree.column('zone', width=200, stretch=False)
        self.zone_tree.column('arguments', width=560)
        self.zone_tree.grid(row=0, column=0, columnspan=3, sticky='ew')
        self.zone_tree.bind('<<TreeviewSelect>>', lambda event: self._zone_selected())
        self.zone_name = tk.StringVar(value='')
        self.zone_text = tk.StringVar(value='')
        ttk.Label(frame, text='Zone:').grid(row=1, column=0, sticky='w', pady=2)
        self.zone_combo = ttk.Combobox(frame, textvariable=self.zone_name, values=[], width=32)
        self.zone_combo.grid(row=1, column=1, sticky='w', pady=2)
        find = ttk.Button(frame, text='Find the occupied zones', command=self.find_zones)
        find.grid(row=1, column=2, sticky='w', padx=6)
        ttk.Label(frame, text='Arguments:').grid(row=2, column=0, sticky='w', pady=2)
        text = ttk.Entry(frame, textvariable=self.zone_text)
        text.grid(row=2, column=1, columnspan=2, sticky='ew', pady=2)
        ttk.Label(frame, text='Pairs name=value separated by commas, for instance comfort_standard=2, category=80, '
                              'comfort_mode=3, hvac_mode=0. The arguments of a zone: '
                              + ', '.join(forms.ZONE_ARGUMENTS) + '.',
                  wraplength=780, foreground='gray25').grid(row=3, column=0, columnspan=3, sticky='w')
        buttons = ttk.Frame(frame)
        buttons.grid(row=4, column=0, columnspan=3, sticky='w', pady=(4, 0))
        set_button = ttk.Button(buttons, text='Set the zone', command=self.set_zone)
        set_button.pack(side='left')
        remove_button = ttk.Button(buttons, text='Remove the selected zones', command=self.remove_zones)
        remove_button.pack(side='left', padx=6)
        self.zone_widgets = [find, text, set_button, remove_button]
        return frame

    def selected_standards(self) -> List[int]:
        return [self.standards[index][0] for index in self.standard_list.curselection()]

    def refresh_idfs(self) -> None:
        """List the input IDFs of the folder, all selected."""
        _fill_list(self.idf_list, forms.input_idfs(self.folder.get()))

    def update_state(self) -> None:
        """Enable the fields that apply to the script type, the setpoint type and the comfort standards."""
        script_type = self.vars['script_type'].get()
        self.script_description.configure(text=forms.SCRIPT_TYPES.get(script_type, ''))
        _set_state([self.supply_air], script_type.startswith('vrf'))
        _set_state(self.mixed_mode_widgets, script_type in forms.MIXED_MODE_SCRIPT_TYPES)
        temperature = self.vars['setpoint_type'].get() == 'temperature'
        _set_state(self.comfort_widgets, temperature)
        _set_state(self.zone_widgets, temperature)
        # The zone can also be typed, so its field is not read-only
        self.zone_combo.configure(state='normal' if temperature else 'disabled')
        standards = self.selected_standards() if temperature else []
        _set_state(self.custom_widgets, 99 in standards)
        self.categories.configure(text=forms.categories_hint(standards))
        self.comfort_modes.configure(text=forms.comfort_modes_hint(standards))

    def zone_rows(self) -> List[Tuple[str, str]]:
        """The rows of the table of the zones: (zone, text of its arguments)."""
        return [tuple(str(value) for value in self.zone_tree.item(item, 'values'))
                for item in self.zone_tree.get_children()]

    def _zone_selected(self) -> None:
        selection = self.zone_tree.selection()
        if selection:
            zone, text = self.zone_tree.item(selection[0], 'values')
            self.zone_name.set(zone)
            self.zone_text.set(text)

    def set_zone(self) -> bool:
        """Add the zone of the fields to the table, or replace its arguments."""
        zone, text = self.zone_name.get().strip(), self.zone_text.get().strip()
        try:
            if not zone:
                raise forms.FormError('zone_arguments: choose or enter the zone.')
            forms.parse_zone_arguments(text, zone)
        except forms.FormError as error:
            self.app.show_error('Arguments of a zone', str(error))
            return False
        for item in self.zone_tree.get_children():
            if str(self.zone_tree.item(item, 'values')[0]).upper() == zone.upper():
                self.zone_tree.item(item, values=(zone, text))
                return True
        self.zone_tree.insert('', 'end', values=(zone, text))
        return True

    def remove_zones(self) -> None:
        for item in self.zone_tree.selection():
            self.zone_tree.delete(item)

    def find_zones(self) -> bool:
        """List the occupied zones of the first selected input IDF in the field of the zone (in a thread)."""
        idfs = _selected(self.idf_list)
        if not idfs:
            self.app.show_error('Find the occupied zones', 'Select an input IDF first.')
            return False
        version = self.vars['energyplus_version'].get()

        def done(zones):
            self.zone_combo.configure(values=zones)
            if zones and not self.zone_name.get():
                self.zone_name.set(zones[0])
            self.app.log_text(f'The occupied zones of {idfs[0]} are: {", ".join(zones)}\n')

        return self.app.run_task('Find the occupied zones', self.folder.get(),
                                 lambda: tasks.occupied_zones(idfs[0], version), on_done=done)

    def form(self) -> Dict[str, Any]:
        """The values of the form, for :func:`accim.gui.forms.add_accis_arguments`."""
        values: Dict[str, Any] = {name: variable.get() for name, variable in self.vars.items()}
        values.update(
            folder=self.folder.get(),
            idfs=_selected(self.idf_list),
            output_frequencies=[f for f, variable in self.frequencies.items() if variable.get()],
            comfort_standard=self.selected_standards(),
            hvac_mode=[m for m, variable in self.hvac_modes.items() if variable.get()],
            ventilation_control=[c for c, variable in self.ventilation_controls.items() if variable.get()],
            zone_arguments=self.zone_rows() if values['setpoint_type'] == 'temperature' else [],
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


class ApmvTab(_Tab):
    """Apply the setpoints based on the adaptive predicted mean vote (aPMV) to an IDF of the folder
    (:mod:`accim.sim.apmv`)."""

    def __init__(self, app: 'AccimApp'):
        super().__init__(app, '2. aPMV setpoints', scrollable=True)
        defaults = forms.APMV_DEFAULTS
        body = self.body
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        self.vars: Dict[str, tk.Variable] = {}
        for name in ('idf', 'output_idf', 'energyplus_version', 'supply_air_temp_input_method',
                     *forms.APMV_SETPOINT_FIELDS, 'cooling_season_start', 'cooling_season_end',
                     *forms.PMV_INPUT_FIELDS):
            self.vars[name] = tk.StringVar(value=defaults[name])
        for name in ('add_vrf_system', 'always_occupied', 'other_pmv_related_outputs'):
            self.vars[name] = tk.BooleanVar(value=defaults[name])
        self.frequencies = {f: tk.BooleanVar(value=f in defaults['output_frequencies'])
                            for f in forms.OUTPUT_FREQUENCIES}
        self._folder_row(0, 'Working folder (input IDFs):', refresh=True)

        model = ttk.LabelFrame(body, text='Model', padding=6)
        model.grid(row=1, column=0, sticky='nsew', padx=(0, 6), pady=4)
        model.columnconfigure(1, weight=1)
        self.idf_combo = _grid_combo(model, 0, 'Input IDF:', self.vars['idf'], [])
        _grid_entry(model, 1, 'Output IDF (empty: <input>_aPMV.idf):', self.vars['output_idf'])
        _grid_combo(model, 2, 'EnergyPlus version:', self.vars['energyplus_version'], forms.ENERGYPLUS_VERSIONS)
        ttk.Checkbutton(model, text='Add a VRF system to each occupied zone (add_vrf_system)',
                        variable=self.vars['add_vrf_system'], command=self.update_state).grid(
            row=3, column=0, columnspan=2, sticky='w')
        self.supply_air = _grid_combo(model, 4, 'Supply air temperature input:',
                                      self.vars['supply_air_temp_input_method'], forms.SUPPLY_AIR_TEMP_INPUT_METHODS)
        ttk.Checkbutton(model, text='Occupants always present (set_zones_always_occupied)',
                        variable=self.vars['always_occupied']).grid(row=5, column=0, columnspan=2, sticky='w')
        ttk.Label(model, text='Output frequencies:').grid(row=6, column=0, sticky='nw', pady=2)
        checks = ttk.Frame(model)
        checks.grid(row=6, column=1, sticky='w')
        for column, (frequency, variable) in enumerate(self.frequencies.items()):
            ttk.Checkbutton(checks, text=frequency, variable=variable).grid(row=column // 3, column=column % 3,
                                                                           sticky='w', padx=(0, 6))
        ttk.Checkbutton(model, text='Other outputs of the PMV (Fanger PMV and PPD...)',
                        variable=self.vars['other_pmv_related_outputs']).grid(row=7, column=0, columnspan=2,
                                                                              sticky='w')

        setpoints = ttk.LabelFrame(body, text='aPMV setpoints (the same in all the zones)', padding=6)
        setpoints.grid(row=1, column=1, sticky='nsew', pady=4)
        setpoints.columnconfigure(1, weight=1)
        for row, (name, label) in enumerate(forms.APMV_SETPOINT_FIELDS.items()):
            _grid_entry(setpoints, row, f'{label}:', self.vars[name], width=10)
        row = len(forms.APMV_SETPOINT_FIELDS)
        _grid_entry(setpoints, row, 'Cooling season from (dd/mm or day):', self.vars['cooling_season_start'],
                    width=10)
        _grid_entry(setpoints, row + 1, 'to (dd/mm or day):', self.vars['cooling_season_end'], width=10)

        pmv = ttk.LabelFrame(body, text='Inputs of the PMV of the occupants (empty: those of the model)', padding=6)
        pmv.grid(row=2, column=0, columnspan=2, sticky='ew', pady=4)
        for index, (name, label) in enumerate(forms.PMV_INPUT_FIELDS.items()):
            _grid_entry(pmv, index // 2, f'{label}:', self.vars[name], width=10, column=(index % 2) * 2)
        pmv.columnconfigure(2, pad=24)

        buttons = ttk.Frame(body)
        buttons.grid(row=3, column=0, columnspan=2, sticky='w', pady=6)
        ttk.Button(buttons, text='Apply the aPMV setpoints', command=self.apply).pack(side='left')
        ttk.Label(body, text='The aPMV corrects the PMV for the adaptation of the occupants: aPMV = PMV / (1 + λ·PMV), '
                             'with one λ for the cooling season and another for the heating season. The thermostats '
                             'keep the aPMV of each zone between the heating and cooling setpoints. Different values '
                             'for each zone need Python (section 4.8 of the documentation). To simulate the new IDF '
                             'in the tab "4. Run the simulations", uncheck "Only the output IDFs of accim".',
                  foreground='gray25', wraplength=900).grid(row=4, column=0, columnspan=2, sticky='w')
        self.update_state()

    def refresh(self) -> None:
        """List the input IDFs of the folder."""
        idfs = forms.input_idfs(self.folder.get())
        self.idf_combo.configure(values=idfs)
        if self.vars['idf'].get() not in idfs:
            self.vars['idf'].set(idfs[0] if idfs else '')

    def update_state(self) -> None:
        _set_state([self.supply_air], self.vars['add_vrf_system'].get())

    def form(self) -> Dict[str, Any]:
        """The values of the form, for :func:`accim.gui.forms.apmv_arguments`."""
        values: Dict[str, Any] = {name: variable.get() for name, variable in self.vars.items()}
        values.update(folder=self.folder.get(),
                      output_frequencies=[f for f, variable in self.frequencies.items() if variable.get()])
        return values

    def apply(self) -> bool:
        """Apply the aPMV setpoints to the input IDF and save it with the new name (in a thread)."""
        try:
            arguments = forms.apmv_arguments(self.form())
        except forms.FormError as error:
            self.app.show_error('aPMV setpoints', str(error))
            return False
        question = f'Apply the aPMV setpoints to {arguments["idf"]} and save it as {arguments["output_idf"]}?'
        if os.path.exists(os.path.join(self.folder.get(), arguments['output_idf'])):
            question += f' {arguments["output_idf"]} will be overwritten.'
        if not self.app.ask_yes_no('aPMV setpoints', question):
            return False

        def done(name):
            self.app.folder_changed()
            self.app.show_info('aPMV setpoints', f'{name} has been written.')

        return self.app.run_task('aPMV setpoints', self.folder.get(), lambda: tasks.apply_apmv(arguments),
                                 on_done=done)


class RenameEpwsTab(_Tab):
    """Rename the EPW files of a folder (:class:`accim.data.preprocessing.rename_epw_files`)."""

    def __init__(self, app: 'AccimApp'):
        super().__init__(app, '3. Rename the EPWs')
        body = self.body
        body.columnconfigure(0, weight=1)
        self._folder_row(0, 'Working folder (EPW files):', refresh=True)
        frame, self.epw_list = _list_frame(body, 'EPW files to rename (the selected ones)', height=6)
        frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=4)
        ttk.Label(body, text='Cities (optional), one per line: text in the name of the EPW = city').grid(
            row=2, column=0, sticky='w', pady=(6, 2))
        self.cities = tk.Text(body, height=4, width=70)
        self.cities.grid(row=3, column=0, sticky='ew')
        ttk.Label(body, text='Countries (optional), one per line: country = city, city...').grid(
            row=4, column=0, sticky='w', pady=(6, 2))
        self.countries = tk.Text(body, height=3, width=70)
        self.countries.grid(row=5, column=0, sticky='ew')
        self.delete_originals = tk.BooleanVar(value=forms.RENAME_EPWS_DEFAULTS['delete_originals'])
        ttk.Checkbutton(body, text='Delete the original EPW files (they are copied with the new names)',
                        variable=self.delete_originals).grid(row=6, column=0, sticky='w', pady=4)
        ttk.Button(body, text='Rename the EPWs', command=self.rename).grid(row=7, column=0, sticky='w', pady=4)
        ttk.Label(body, text='The new names follow Country_City_Scenario-Year: the scenario and the year are read from '
                             'the name of each EPW (Present if it has none), and the country and the city from its '
                             'coordinates, in OpenStreetMap, which needs internet; the cities and countries above give '
                             'them instead. Table splits these names with "Split the names of the EPWs". If '
                             'OpenStreetMap does not give the city or the country of an EPW, or two EPWs would get the '
                             'same name, the renaming stops: give their cities and countries above.',
                  foreground='gray25', wraplength=900).grid(row=8, column=0, sticky='w')

    def refresh(self) -> None:
        """List the EPWs of the folder, all selected."""
        _fill_list(self.epw_list, forms.epw_files(self.folder.get()))

    def form(self) -> Dict[str, Any]:
        """The values of the form, for :func:`accim.gui.forms.rename_epws_arguments`."""
        return dict(folder=self.folder.get(), epws=_selected(self.epw_list), cities=self.cities.get('1.0', 'end'),
                    countries=self.countries.get('1.0', 'end'), delete_originals=self.delete_originals.get())

    def rename(self) -> bool:
        """Rename the selected EPWs (in a thread)."""
        try:
            arguments = forms.rename_epws_arguments(self.form())
        except forms.FormError as error:
            self.app.show_error('Rename the EPWs', str(error))
            return False
        question = f'Copy the {len(arguments["filelist"])} selected EPW files with their new names?'
        if arguments['confirm_deletion']:
            question += ' The original files will be deleted.'
        if not self.app.ask_yes_no('Rename the EPWs', question):
            return False
        return self.app.run_task('Rename the EPWs', self.folder.get(), lambda: tasks.rename_epws(arguments),
                                 on_done=lambda epws: self.app.folder_changed(), answers=tasks.RENAME_EPWS_ANSWERS)


class RunTab(_Tab):
    """Run the simulations of the IDFs and EPWs of a folder (:func:`accim.run.run_ep`)."""

    def __init__(self, app: 'AccimApp'):
        super().__init__(app, '4. Run the simulations')
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
        self.only_accim_idfs_check = ttk.Checkbutton(body, text="Only the output IDFs of accim (with '[' in the name)",
                                                     variable=self.vars['only_accim_idfs'], command=self.preview)
        self.only_accim_idfs_check.grid(row=1, column=0, columnspan=2, sticky='w', pady=2)
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

        return self.app.run_task('Run the simulations', self.folder.get(), task,
                                 on_done=lambda result: self.app.folder_changed())

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
        super().__init__(app, '5. Hours within the setpoints')
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
        self.tree = _tree(body)
        self.tree.master.grid(row=4, column=0, columnspan=2, sticky='nsew')
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


class TableTab(_Tab):
    """Tables and figures of the results of the simulations of a folder
    (:class:`accim.data.postprocessing.main.Table`)."""

    def __init__(self, app: 'AccimApp'):
        super().__init__(app, '6. Table and figures', scrollable=True)
        defaults = forms.TABLE_DEFAULTS
        body = self.body
        body.columnconfigure(0, weight=1)
        self.vars: Dict[str, tk.Variable] = {
            name: tk.StringVar(value=defaults[name])
            for name in ('idf_path', 'source_frequency', 'frequency', 'frequency_agg_func', 'level_excluded_zones',
                         'type_of_table', 'figure_type', 'y_axis_label', 'figname', 'figsize', 'dpi')}
        self.vars['data_on_x_axis'] = tk.StringVar(value='')
        for name in ('standard_outputs', 'split_epw_names'):
            self.vars[name] = tk.BooleanVar(value=defaults[name])
        self.levels = {level: tk.BooleanVar(value=level in defaults['level']) for level in ('block', 'building')}
        self.level_funcs = {func: tk.BooleanVar(value=func in defaults['level_agg_func']) for func in ('sum', 'mean')}
        self.table = None
        self.table_type = defaults['type_of_table']
        self._folder_row(0, 'Working folder (CSV files of the simulations):', refresh=True)

        frame = ttk.LabelFrame(body, text='Table', padding=6)
        frame.grid(row=1, column=0, sticky='ew', pady=4)
        frame.columnconfigure(1, weight=1)
        self.idf_combo = _grid_combo(frame, 0, 'IDF of the building (for its zones):', self.vars['idf_path'], [],
                                     width=50)
        _grid_combo(frame, 1, 'Frequency of the CSV files:', self.vars['source_frequency'],
                    forms.TABLE_FREQUENCIES).grid(sticky='w')
        _grid_combo(frame, 2, 'Frequency of the table:', self.vars['frequency'], forms.TABLE_FREQUENCIES).grid(
            sticky='w')
        _grid_combo(frame, 3, 'Aggregation of the rows:', self.vars['frequency_agg_func'], ('sum', 'mean')).grid(
            sticky='w')
        checks = ttk.Frame(frame)
        checks.grid(row=4, column=0, columnspan=2, sticky='w', pady=2)
        ttk.Checkbutton(checks, text='Standard outputs only', variable=self.vars['standard_outputs']).pack(
            side='left')
        ttk.Checkbutton(checks, text='Split the names of the EPWs (Country_City_Scenario-Year)',
                        variable=self.vars['split_epw_names']).pack(side='left', padx=12)
        levels = ttk.Frame(frame)
        levels.grid(row=5, column=0, columnspan=2, sticky='w', pady=2)
        ttk.Label(levels, text='Totals of:').pack(side='left')
        for level, variable in self.levels.items():
            ttk.Checkbutton(levels, text=level, variable=variable).pack(side='left', padx=(6, 0))
        ttk.Label(levels, text='   as:').pack(side='left')
        for func, variable in self.level_funcs.items():
            ttk.Checkbutton(levels, text=func, variable=variable).pack(side='left', padx=(6, 0))
        _grid_entry(frame, 6, 'Zones left out of the totals (separated by commas):',
                    self.vars['level_excluded_zones'])
        _grid_combo(frame, 7, 'Columns of the table:', self.vars['type_of_table'], forms.TABLE_TYPES).grid(sticky='w')
        buttons = ttk.Frame(frame)
        buttons.grid(row=8, column=0, columnspan=2, sticky='w', pady=(6, 0))
        ttk.Button(buttons, text='Make the table', command=self.make_table).pack(side='left')
        self.export_button = ttk.Button(buttons, text='Export the table...', command=self.export, state='disabled')
        self.export_button.pack(side='left', padx=6)
        self.summary = tk.StringVar(value='')
        ttk.Label(frame, textvariable=self.summary, wraplength=900).grid(row=9, column=0, columnspan=2, sticky='w')

        self.tree = _tree(body, height=8)
        self.tree.master.grid(row=2, column=0, sticky='nsew', pady=4)

        figure = ttk.LabelFrame(body, text='Figure (Table.scatter_plot or Table.time_plot), saved as a PNG file in '
                                           'the folder', padding=6)
        figure.grid(row=3, column=0, sticky='ew', pady=4)
        for column in range(3):
            figure.columnconfigure(column, weight=1)
        _grid_combo(figure, 0, 'Figure:', self.vars['figure_type'], forms.FIGURE_TYPES).grid(sticky='w')
        lists = ttk.Frame(figure)
        lists.grid(row=1, column=0, columnspan=3, sticky='ew', pady=4)
        for column in range(3):
            lists.columnconfigure(column, weight=1)
        self.rows_list = self._choice_list(lists, 0, 'Rows of subplots')
        self.cols_list = self._choice_list(lists, 1, 'Columns of subplots')
        self.y_list = self._choice_list(lists, 2, 'Columns of the y axis')
        self.x_combo = _grid_combo(figure, 2, 'Column of the x axis (scatter plot):', self.vars['data_on_x_axis'], [],
                                   width=60)
        _grid_entry(figure, 3, 'Label of the y axis:', self.vars['y_axis_label'])
        _grid_entry(figure, 4, 'Name of the file (without .png):', self.vars['figname'])
        _grid_entry(figure, 5, 'Width of each subplot (inches):', self.vars['figsize'], width=8).grid(sticky='w')
        _grid_entry(figure, 6, 'Resolution (dpi):', self.vars['dpi'], width=8).grid(sticky='w')
        self.figure_button = ttk.Button(figure, text='Make the figure', command=self.make_figure, state='disabled')
        self.figure_button.grid(row=7, column=0, sticky='w', pady=(6, 0))
        ttk.Label(figure, text='The subplots group the simulations by the variables whose values differ between them '
                               '(the comfort standard, the category, the EPW...). The other figures and the reshaping '
                               'of the tables (wrangled_table) need Python: see the notebook of Table.',
                  foreground='gray25', wraplength=900).grid(row=8, column=0, columnspan=3, sticky='w')
        self.vars['figure_type'].trace_add('write', lambda *args: self.update_state())
        self.update_state()

    @staticmethod
    def _choice_list(parent, column: int, text: str) -> tk.Listbox:
        frame = ttk.LabelFrame(parent, text=text, padding=4)
        frame.grid(row=0, column=column, sticky='nsew', padx=(0, 6))
        frame.columnconfigure(0, weight=1)
        listbox = tk.Listbox(frame, selectmode='extended', height=6, exportselection=False)
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        listbox.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        return listbox

    def update_state(self) -> None:
        _set_state([self.x_combo], self.vars['figure_type'].get() == 'scatter')

    def refresh(self) -> None:
        """List the IDFs of the folder, and count the CSV files of its simulations."""
        folder = self.folder.get()
        idfs = forms.idf_files(folder)
        self.idf_combo.configure(values=idfs)
        if self.vars['idf_path'].get() not in idfs:
            inputs = forms.input_idfs(folder)
            self.vars['idf_path'].set(inputs[0] if inputs else idfs[0] if idfs else '')
        if self.table is None:
            self.summary.set(f'{len(forms.simulation_csvs(folder))} CSV files of simulations in the folder.')

    def form(self) -> Dict[str, Any]:
        """The values of the form, for :func:`accim.gui.forms.table_arguments` and
        :func:`accim.gui.forms.figure_arguments`."""
        values: Dict[str, Any] = {name: variable.get() for name, variable in self.vars.items()}
        values.update(
            folder=self.folder.get(),
            level=[level for level, variable in self.levels.items() if variable.get()],
            level_agg_func=[func for func, variable in self.level_funcs.items() if variable.get()],
            vars_to_gather_rows=_selected(self.rows_list),
            vars_to_gather_cols=_selected(self.cols_list),
            data_on_y_main_axis=_selected(self.y_list),
            table_frequency=getattr(self.table, 'frequency', '') if self.table is not None else '',
        )
        return values

    def make_table(self) -> bool:
        """Make the table of the CSV files of the folder (in a thread)."""
        try:
            arguments = forms.table_arguments(self.form())
        except forms.FormError as error:
            self.app.show_error('Table', str(error))
            return False
        self.table_type = arguments['type_of_table']
        return self.app.run_task('Table', self.folder.get(), lambda: tasks.make_table(arguments),
                                 on_done=self.show_table)

    def show_table(self, table) -> None:
        """Show the table, and the columns that the figures can use."""
        self.table = table
        df = table.df
        variables = list(getattr(table, 'cols_for_multiindex', []) or [])
        value_columns = [str(c) for c in (getattr(table, 'val_cols', None) or df.select_dtypes('number').columns)]
        _show_dataframe(self.tree, df)
        _fill_list(self.rows_list, variables, select_all=False)
        _fill_list(self.cols_list, variables, select_all=False)
        _fill_list(self.y_list, value_columns, select_all=False)
        self.x_combo.configure(values=value_columns)
        if self.vars['data_on_x_axis'].get() not in value_columns:
            self.vars['data_on_x_axis'].set(value_columns[0] if value_columns else '')
        differing = '; '.join(f'{name}: {", ".join(str(v) for v in values)}'
                              for name, values in (getattr(table, 'suggested_vars_dict', {}) or {}).items())
        shown = f' (the first {MAX_ROWS_SHOWN} are shown)' if len(df) > MAX_ROWS_SHOWN else ''
        self.summary.set(f'{len(df)} rows{shown} and {len(df.columns)} columns. The variables whose values differ '
                         f'between the simulations: {differing or "none (the figures need at least two)"}.')
        self.export_button.state(['!disabled'])
        self.figure_button.state(['!disabled'])

    def export(self) -> None:
        if self.table is not None:
            _export_dataframe(self.app, self.table.df, self.folder.get(), 'accim_table.csv')

    def make_figure(self) -> bool:
        """Make the figure of the table, save it in the folder and open it (in a thread)."""
        if self.table is None:
            self.app.show_error('Figure', 'Make the table first.')
            return False
        try:
            arguments = forms.figure_arguments(self.form())
        except forms.FormError as error:
            self.app.show_error('Figure', str(error))
            return False
        table, table_type = self.table, self.table_type

        def task():
            # The figures filter the rows of the table: each one starts from the whole table
            table.format_table(type_of_table=table_type)
            return tasks.make_figure(table, arguments)

        return self.app.run_task('Figure', self.folder.get(), task, on_done=_open_file,
                                 answers=tasks.FIGURE_ANSWERS)


class ParametricTab(_Tab):
    """A basic parametric study of the accim models
    (:class:`accim.parametric_and_optimisation.main.ParametricSimulation`)."""

    def __init__(self, app: 'AccimApp'):
        super().__init__(app, '7. Parametric study', scrollable=True)
        defaults = forms.PARAMETRIC_DEFAULTS
        body = self.body
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        self.vars: Dict[str, tk.Variable] = {
            name: tk.StringVar(value=defaults[name])
            for name in ('idf', 'parameters_type', 'script_type', 'sampling', 'samples', 'meters', 'processes',
                         'out_dir')}
        self.results = None
        self._folder_row(0, 'Working folder (IDF and EPWs):', refresh=True)

        model = ttk.LabelFrame(body, text='Model and weather', padding=6)
        model.grid(row=1, column=0, sticky='nsew', padx=(0, 6), pady=4)
        model.columnconfigure(1, weight=1)
        self.idf_combo = _grid_combo(model, 0, 'Input IDF:', self.vars['idf'], [])
        _grid_combo(model, 1, 'Parameters:', self.vars['parameters_type'], forms.PARAMETERS_TYPES)
        _grid_combo(model, 2, 'Script type:', self.vars['script_type'], forms.PARAMETRIC_SCRIPT_TYPES)
        epws, self.epw_list = _list_frame(model, 'EPW files (the selected ones)', height=4)
        epws.grid(row=3, column=0, columnspan=2, sticky='ew', pady=(4, 0))

        parameters = ttk.LabelFrame(body, text='Parameters of the study', padding=6)
        parameters.grid(row=1, column=1, sticky='nsew', pady=4)
        parameters.columnconfigure(1, weight=1)
        self.parameter_tree = ttk.Treeview(parameters, columns=('name', 'values'), show='headings', height=5)
        self.parameter_tree.heading('name', text='Parameter')
        self.parameter_tree.heading('values', text='Values')
        self.parameter_tree.column('name', width=200, stretch=False)
        self.parameter_tree.column('values', width=200)
        self.parameter_tree.grid(row=0, column=0, columnspan=3, sticky='ew')
        self.parameter_tree.bind('<<TreeviewSelect>>', lambda event: self._parameter_selected())
        self.parameter_name = tk.StringVar(value='')
        self.parameter_values = tk.StringVar(value='')
        self.parameter_combo = _grid_combo(parameters, 1, 'Parameter:', self.parameter_name, [])
        _grid_entry(parameters, 2, 'Values:', self.parameter_values)
        buttons = ttk.Frame(parameters)
        buttons.grid(row=3, column=0, columnspan=3, sticky='w', pady=(4, 0))
        ttk.Button(buttons, text='Set the parameter', command=self.set_parameter).pack(side='left')
        ttk.Button(buttons, text='Remove the selected parameters', command=self.remove_parameters).pack(
            side='left', padx=6)
        ttk.Label(parameters, text='Options, separated by commas (1, 2, 3), for the full set; or a range (0.2 to 0.6) '
                                   'for the Latin hypercube sample of the custom models.', foreground='gray25',
                  wraplength=420).grid(row=4, column=0, columnspan=3, sticky='w')

        plan = ttk.LabelFrame(body, text='Plan, outputs and run', padding=6)
        plan.grid(row=2, column=0, columnspan=2, sticky='ew', pady=4)
        plan.columnconfigure(1, weight=1)
        _grid_combo(plan, 0, 'Plan:', self.vars['sampling'], forms.SAMPLINGS).grid(sticky='w')
        self.samples_entry = _grid_entry(plan, 1, 'Number of samples (Latin hypercube):', self.vars['samples'],
                                         width=8)
        self.samples_entry.grid(sticky='w')
        _grid_entry(plan, 2, 'Meters of the results (separated by commas):', self.vars['meters'])
        ttk.Label(plan, text='Simulations at the same time:').grid(row=3, column=0, sticky='w', pady=2)
        ttk.Spinbox(plan, from_=1, to=max(os.cpu_count() or 1, 1), textvariable=self.vars['processes'],
                    width=6).grid(row=3, column=1, sticky='w', pady=2)
        _grid_entry(plan, 4, 'Folder of the results (in the working folder):', self.vars['out_dir'])
        run_buttons = ttk.Frame(plan)
        run_buttons.grid(row=5, column=0, columnspan=2, sticky='w', pady=(6, 0))
        ttk.Button(run_buttons, text='Run the parametric study', command=self.run).pack(side='left')
        self.export_button = ttk.Button(run_buttons, text='Export the results...', command=self.export,
                                        state='disabled')
        self.export_button.pack(side='left', padx=6)
        self.count = tk.StringVar(value='')
        ttk.Label(plan, textvariable=self.count, wraplength=900).grid(row=6, column=0, columnspan=2, sticky='w')

        self.tree = _tree(body, height=8)
        self.tree.master.grid(row=3, column=0, columnspan=2, sticky='nsew', pady=4)
        ttk.Label(body, text='The model gets accim with each combination of the parameters (the coefficients of the '
                             'custom model that are not parameters take the default values), and the results are the '
                             'sums of the meters over the run period of each simulation. Other outputs, objectives, '
                             'optimisations, the m-n filter and the plots need Python: see the parametric and '
                             'optimisation section of the documentation.',
                  foreground='gray25', wraplength=900).grid(row=4, column=0, columnspan=2, sticky='w')
        self.vars['parameters_type'].trace_add('write', lambda *args: self.update_state())
        self.vars['sampling'].trace_add('write', lambda *args: self.update_state())
        self.update_state()

    def update_state(self) -> None:
        """The parameters of the type of model, and the number of samples only for the Latin hypercube."""
        names = list(forms.PARAMETERS_TYPES.get(self.vars['parameters_type'].get(), ()))
        self.parameter_combo.configure(values=names)
        if self.parameter_name.get() not in names:
            self.parameter_name.set(names[0] if names else '')
        _set_state([self.samples_entry], self.vars['sampling'].get() == 'lhs')

    def refresh(self) -> None:
        """List the input IDFs and the EPWs of the folder."""
        folder = self.folder.get()
        idfs = forms.input_idfs(folder)
        self.idf_combo.configure(values=idfs)
        if self.vars['idf'].get() not in idfs:
            self.vars['idf'].set(idfs[0] if idfs else '')
        _fill_list(self.epw_list, forms.epw_files(folder))

    def parameter_rows(self) -> List[Tuple[str, str]]:
        """The rows of the table of the parameters: (name, values)."""
        return [tuple(str(value) for value in self.parameter_tree.item(item, 'values'))
                for item in self.parameter_tree.get_children()]

    def _parameter_selected(self) -> None:
        selection = self.parameter_tree.selection()
        if selection:
            name, values = self.parameter_tree.item(selection[0], 'values')
            self.parameter_name.set(name)
            self.parameter_values.set(values)

    def set_parameter(self) -> bool:
        """Add the parameter of the fields to the table, or replace its values."""
        name, text = self.parameter_name.get().strip(), self.parameter_values.get().strip()
        try:
            if not name:
                raise forms.FormError('parameters: choose the parameter.')
            forms.parse_parameter_values(text, name)
        except forms.FormError as error:
            self.app.show_error('Parameter', str(error))
            return False
        for item in self.parameter_tree.get_children():
            if self.parameter_tree.item(item, 'values')[0] == name:
                self.parameter_tree.item(item, values=(name, text))
                return True
        self.parameter_tree.insert('', 'end', values=(name, text))
        return True

    def remove_parameters(self) -> None:
        for item in self.parameter_tree.selection():
            self.parameter_tree.delete(item)

    def form(self) -> Dict[str, Any]:
        """The values of the form, for :func:`accim.gui.forms.parametric_arguments`."""
        values: Dict[str, Any] = {name: variable.get() for name, variable in self.vars.items()}
        values.update(folder=self.folder.get(), epws=_selected(self.epw_list), parameters=self.parameter_rows())
        return values

    def run(self) -> bool:
        """Run the parametric study (in a thread)."""
        try:
            arguments = forms.parametric_arguments(self.form())
        except forms.FormError as error:
            self.app.show_error('Parametric study', str(error))
            return False
        count = forms.parametric_simulation_count(arguments)
        self.count.set(f'At most {count} simulations (the invalid combinations of the predefined models are '
                       f'left out), and a short test simulation that finds the outputs.')
        if not self.app.ask_yes_no('Parametric study', f'Run up to {count} simulations, with the results in '
                                                       f'{arguments["out_dir"]}?'):
            return False
        return self.app.run_task('Parametric study', self.folder.get(), lambda: tasks.parametric_study(arguments),
                                 on_done=self.show_results)

    def show_results(self, results) -> None:
        self.results = results
        _show_dataframe(self.tree, results)
        self.count.set(f'{len(results)} simulations; the results are also in the folder of the results.')
        self.export_button.state(['!disabled'])

    def export(self) -> None:
        if self.results is not None:
            _export_dataframe(self.app, self.results, self.folder.get(), 'accim_parametric_results.csv')


class AccimApp:
    """The main window of the graphical user interface of accim.

    :param root: The tkinter window; a new one if None.
    :ivar add_accis: The tab that adds the ACCIS.
    :ivar apmv: The tab of the aPMV setpoints.
    :ivar rename_epws: The tab that renames the EPW files.
    :ivar run: The tab that runs the simulations.
    :ivar hours: The tab of the occupied hours within the setpoints.
    :ivar table: The tab of the tables and figures of the results.
    :ivar parametric: The tab of the parametric study.
    """

    def __init__(self, root: Optional[tk.Tk] = None):
        self.root = root if root is not None else tk.Tk()
        self.root.title(f'accim {__version__}: Adaptive-Comfort-Control-Implemented Model')
        self.root.geometry('1250x850')
        self.root.minsize(800, 600)
        self.messages: queue.Queue = queue.Queue()
        self.busy = False
        #: The working folder of the tabs
        self.folder = tk.StringVar(value=os.getcwd())
        panes = ttk.PanedWindow(self.root, orient='vertical')
        panes.pack(fill='both', expand=True, padx=6, pady=6)
        self.notebook = ttk.Notebook(panes)
        panes.add(self.notebook, weight=3)
        self.add_accis = AddAccisTab(self)
        self.apmv = ApmvTab(self)
        self.rename_epws = RenameEpwsTab(self)
        self.run = RunTab(self)
        self.hours = HoursTab(self)
        self.table = TableTab(self)
        self.parametric = ParametricTab(self)
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
        """List the files of the working folder again (the IDFs, EPWs and results of the tabs)."""
        self.add_accis.refresh_idfs()
        self.apmv.refresh()
        self.rename_epws.refresh()
        self.run.preview()
        self.table.refresh()
        self.parametric.refresh()

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
                 on_done: Optional[Callable[[Any], None]] = None,
                 answers: Optional[Mapping[str, str]] = None) -> bool:
        """Run a task in a thread, in a folder; its output goes to the log, and ``on_done(result)`` runs when it ends.

        :param answers: The answers to the questions of the prompt that the task asks (the beginning of each question
            -> its answer); the other questions stop the task with an error.
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
        threading.Thread(target=self.execute, args=(title, folder, function, on_done, answers), daemon=True).start()
        return True

    def execute(self, title: str, folder: str, function: Callable[[], Any],
                on_done: Optional[Callable[[Any], None]] = None,
                answers: Optional[Mapping[str, str]] = None) -> None:
        """Run a task in the current thread: in its folder, with what it prints, and its end, in the queue of
        messages, which :meth:`process_messages` shows."""
        writer = _QueueWriter(self.messages)
        cwd = os.getcwd()
        try:
            with contextlib.redirect_stdout(writer), contextlib.redirect_stderr(writer), _no_prompts(answers):
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
