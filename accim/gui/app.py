# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The graphical user interface of accim, with tkinter: add the ACCIS (with the arguments of each zone) or the
PMV-based setpoints (aPMV, ePMV or PMV, with the setpoints of each zone) to IDF files, read the EMS code of the
setpoints, rename the EPW files, estimate the size of the results and run the simulations, measure the occupied hours
within the setpoints, make tables and figures of the results with ``Table``, and run a basic parametric study.

Open it with ``accim-gui`` (a command installed with accim) or ``python -m accim.gui``. Each task runs in a thread,
one at a time, in the working folder, and what it prints appears in the log at the bottom of the window; when a task
asks a question that the window knows (such as the confirmation of AddAccis after the estimated size of the results),
the window asks it in a dialog. The values of the forms are checked by :mod:`accim.gui.forms`, and the tasks run by
:mod:`accim.gui.tasks`. The menu *Session* saves the values of the forms and the results of the tabs in a session file
(a pickle file, with a JSON file to read it; see :mod:`accim.utils.session`), and opens it again to resume the session.
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
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Tuple

from accim import __version__
from accim.gui import forms, tasks

__all__ = ['AccimApp', 'main']

DOCS_URL = 'https://accim.readthedocs.io/'
#: The number of rows of a table shown in the window (the exported files have all of them)
MAX_ROWS_SHOWN = 500
#: The file types of the dialogs of the session files and of the files of the tables
SESSION_FILE_TYPES = [('Sessions of accim (pickle files)', '*.pkl'), ('All files', '*.*')]
TABLE_FILE_TYPES = [('Tables of accim (pickle files)', '*.pkl'), ('All files', '*.*')]
#: The beginning of the question of AddAccis before it writes the output IDFs, which the window asks in a dialog
ADD_ACCIS_QUESTION = 'Do you still want to run ACCIS?'
#: The lines of the output of AddAccis that the dialog of its question shows, at most
MAX_QUESTION_LINES = 30


class _QueueWriter:
    """A text stream that puts what is written into a queue (the output of a task, for the log), and keeps it
    (:meth:`text`), for the questions that the window asks during the task."""

    def __init__(self, messages: queue.Queue):
        self.messages = messages
        self._written: List[str] = []

    def write(self, text: str) -> int:
        if text:
            self.messages.put(('text', text))
            self._written.append(text)
        return len(text)

    def flush(self) -> None:
        pass

    def text(self) -> str:
        """What the task has printed."""
        return ''.join(self._written)


@contextlib.contextmanager
def _no_prompts(answers: Optional[Mapping[str, Any]] = None, printed: Optional[Callable[[], str]] = None):
    """The interface cannot answer the questions of the prompt: ``input()`` raises an error instead of waiting, except
    for the questions that begin with a key of ``answers``, which get its value (printed after the question, as if it
    was typed). A value can also be a function of the question and of what the task has printed (``printed()``) that
    returns the answer, for instance after asking the user in a dialog (:meth:`AccimApp.ask_from_task`)."""
    original = builtins.input

    def refuse(prompt: str = '') -> str:
        question = str(prompt).strip()
        for beginning, answer in (answers or {}).items():
            if question.startswith(beginning):
                if callable(answer):
                    answer = answer(question, printed() if printed is not None else '')
                print(f'{prompt}{answer}')
                return answer
        raise RuntimeError(f'accim asked in the prompt {question!r}, which the graphical interface cannot answer: '
                           f'check the values of the form.')

    builtins.input = refuse
    try:
        yield
    finally:
        builtins.input = original


def _write_question(printed: str, folder: str, total: int) -> str:
    """The question of the window before AddAccis writes the output IDFs: their number and the estimated size of the
    results of their simulations, as AddAccis has printed them (from 'And the total number of output IDFs' on)."""
    start = printed.rfind('And the total number of output IDFs')
    lines = [line for line in printed[start:].strip().splitlines() if line.strip()] if start >= 0 else []
    if len(lines) > MAX_QUESTION_LINES:
        lines = lines[:MAX_QUESTION_LINES] + ['... (see the log)']
    summary = '\n'.join(lines) if lines else f'AddAccis is going to write {total} output IDFs.'
    return f'{summary}\n\nWrite the output IDFs in {folder}?'


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

    def see(self, widget) -> None:
        """Scroll the content so that a widget of it is at the top."""
        self.update_idletasks()
        height = self.content.winfo_height()
        if height > 0:
            offset = widget.winfo_rooty() - self.content.winfo_rooty()
            self.canvas.yview_moveto(max(0.0, offset / height))


class _Tab:
    """A tab of the notebook; the folder is that of the whole window.

    :param scrollable: True for a tab whose content scrolls vertically (``self.scroll``).
    :param bar: True for a bar of buttons below the content that scrolls, always visible (``self.bar``).
    """

    def __init__(self, app: 'AccimApp', title: str, scrollable: bool = False, bar: bool = False):
        self.app = app
        self.scroll: Optional[_ScrollableFrame] = None
        self.bar: Optional[ttk.Frame] = None
        if scrollable:
            self.frame = ttk.Frame(app.notebook)
            if bar:
                self.bar = ttk.Frame(self.frame, padding=(8, 4, 8, 6))
                self.bar.pack(side='bottom', fill='x')
                ttk.Separator(self.frame, orient='horizontal').pack(side='bottom', fill='x')
            self.scroll = _ScrollableFrame(self.frame)
            self.scroll.pack(fill='both', expand=True)
            self.body = self.scroll.content
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

    def state(self) -> Dict[str, Any]:
        """The values of the fields of the tab, for the session files (:meth:`AccimApp.save_session`)."""
        return _variables_state(getattr(self, 'vars', {}))

    def restore(self, state: Mapping[str, Any]) -> List[str]:
        """Set the fields of the tab to the values of a session (those that it does not have keep theirs).

        :return: The messages of the values that could not be restored (files that are not in the folder).
        """
        _restore_variables(getattr(self, 'vars', {}), state)
        return []


def _folder_of(path: str) -> str:
    """The folder of a file, in which the task that writes or reads it runs."""
    return os.path.dirname(os.path.abspath(path))


def _variables_state(variables: Mapping[str, tk.Variable]) -> Dict[str, Any]:
    """The values of the variables of the fields of a form, by name."""
    return {name: variable.get() for name, variable in variables.items()}


def _restore_variables(variables: Mapping[str, tk.Variable], values: Mapping[str, Any]) -> None:
    """Set the variables of a form that ``values`` has (the others keep their values)."""
    for name, variable in variables.items():
        if name in values:
            variable.set(bool(values[name]) if isinstance(variable, tk.BooleanVar) else values[name])


def _checks_state(checks: Mapping[Any, tk.BooleanVar]) -> List[Any]:
    """The checked options of a group of check buttons."""
    return [option for option, variable in checks.items() if variable.get()]


def _restore_checks(checks: Mapping[Any, tk.BooleanVar], checked) -> None:
    for option, variable in checks.items():
        variable.set(option in checked)


def _select(listbox: tk.Listbox, items, what: str) -> List[str]:
    """Select the items of a list that are in ``items`` (and no other).

    :return: The message of the items that the list does not have, if any.
    """
    present = list(listbox.get(0, 'end'))
    listbox.selection_clear(0, 'end')
    for index, item in enumerate(present):
        if item in items:
            listbox.selection_set(index)
    missing = [str(item) for item in items if item not in present]
    return [f'{what}: {", ".join(missing)} not found.'] if missing else []


def _file_messages(name: str, files, what: str) -> List[str]:
    """The message of a file of a session that is not in the working folder, if it is not."""
    return [f'{what}: {name} not found in the working folder.'] if name and name not in files else []


def _set_rows(tree: ttk.Treeview, rows) -> None:
    """Replace the rows of a table of the window."""
    tree.delete(*tree.get_children())
    for row in rows:
        tree.insert('', 'end', values=tuple(row))


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


def _existing_hvac_widgets(frame, variables: Mapping[str, tk.Variable]) -> Tuple[List[Any], List[Any], ttk.Combobox]:
    """The options of the existing HVAC systems in a frame (forms.EXISTING_HVAC_OPTIONS and the availability schedule):
    return their widgets, those that need the adaptive setpoint temperatures, and the field of the schedule."""
    frame.columnconfigure(1, weight=1)
    widgets: List[Any] = []
    temperature_widgets: List[Any] = []
    for index, (name, label) in enumerate(forms.EXISTING_HVAC_OPTIONS.items()):
        check = ttk.Checkbutton(frame, text=f'{label} ({name})', variable=variables[name])
        check.grid(row=index, column=0, columnspan=2, sticky='w')
        widgets.append(check)
        if name in ('existing_hvac_operative_temperature_control', 'existing_hvac_radiant_setpoints'):
            temperature_widgets.append(check)
    row = len(forms.EXISTING_HVAC_OPTIONS)
    ttk.Label(frame, text='Availability schedule (existing_hvac_availability_schedule; empty: that of the model, '
                          'On 24/7: always available):').grid(row=row, column=0, sticky='w', padx=(0, 6), pady=2)
    combo = ttk.Combobox(frame, textvariable=variables['existing_hvac_availability_schedule'],
                         values=list(forms.EXISTING_HVAC_AVAILABILITY), width=24)
    combo.grid(row=row, column=1, sticky='w', pady=2)
    return widgets, temperature_widgets, combo


def _set_existing_hvac_state(widgets, temperature_widgets, combo: ttk.Combobox, existing: bool,
                             temperature: bool = True) -> None:
    """Enable the options of the existing HVAC systems with their script types (and the options of the setpoints with
    the adaptive setpoint temperatures)."""
    _set_state(widgets, existing)
    _set_state(temperature_widgets, existing and temperature)
    # Any schedule of the model can be typed, so the field is not read-only
    combo.configure(state='normal' if existing else 'disabled')


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


class _ZoneTable:
    """The table of the arguments of some zones of a tab: a row for each zone, with the text of its arguments (pairs
    name=value), and the fields to edit them: the zone (one of the occupied zones of the input IDF, which *Find the
    occupied zones* lists, or typed), a field for each main argument (empty: the value of the form) and the other
    arguments, as pairs name=value. Selecting a row fills the fields with its arguments.

    :param frame: The frame of the table, placed in the tab.
    :param fields: The fields of the main arguments: (argument, label, choices; None for a text field). The fields
        with choices can also be typed.
    :param compose: The text of a row from the values of the fields, the other arguments and the zone, checked
        (:func:`accim.gui.forms.zone_row_text`).
    :param split: The values of the fields and the other arguments of the text of a row
        (:func:`accim.gui.forms.split_zone_arguments`).
    :param find_zones: What *Find the occupied zones* does.
    :param title: The title of the dialogs of the errors.
    :param name: The name of the argument of the table, for the messages ('zone_arguments').
    :param hint: The explanation below the fields.
    :param what: What the arguments are, in the heading of the table and the label of the other ones ('arguments').
    """

    def __init__(self, app: 'AccimApp', frame, fields, compose: Callable, split: Callable,
                 find_zones: Callable[[], Any], title: str, name: str, hint: str, what: str = 'arguments'):
        self.app = app
        self.compose, self.split, self.title, self.name = compose, split, title, name
        self._disabled: set = set()
        frame.columnconfigure(1, weight=1)
        self.tree = ttk.Treeview(frame, columns=('zone', 'arguments'), show='headings', height=4)
        self.tree.heading('zone', text='Zone')
        self.tree.heading('arguments', text=what.capitalize())
        self.tree.column('zone', width=220, stretch=False)
        self.tree.column('arguments', width=700)
        self.tree.grid(row=0, column=0, columnspan=3, sticky='ew')
        self.tree.bind('<<TreeviewSelect>>', lambda event: self._selected())
        self.zone = tk.StringVar(value='')
        ttk.Label(frame, text='Zone:').grid(row=1, column=0, sticky='w', padx=(0, 6), pady=(6, 2))
        self.zone_combo = ttk.Combobox(frame, textvariable=self.zone, values=[], width=40)
        self.zone_combo.grid(row=1, column=1, sticky='w', pady=(6, 2))
        self.find_button = ttk.Button(frame, text='Find the occupied zones', command=find_zones)
        self.find_button.grid(row=1, column=2, sticky='e', padx=(6, 0), pady=(6, 2))
        grid = ttk.Frame(frame)
        grid.grid(row=2, column=0, columnspan=3, sticky='ew')
        grid.columnconfigure(1, weight=1)
        grid.columnconfigure(3, weight=1)
        self.vars: Dict[str, tk.StringVar] = {}
        self.fields: Dict[str, Any] = {}
        for index, (argument, label, choices) in enumerate(fields):
            row, column = divmod(index, 2)
            ttk.Label(grid, text=label).grid(row=row, column=2 * column, sticky='w',
                                             padx=(0 if column == 0 else 18, 6), pady=2)
            variable = tk.StringVar(value='')
            if choices is None:
                widget = ttk.Entry(grid, textvariable=variable, width=14)
            else:
                widget = ttk.Combobox(grid, textvariable=variable, values=list(choices), width=36)
            widget.grid(row=row, column=2 * column + 1, sticky='ew', pady=2)
            self.vars[argument] = variable
            self.fields[argument] = widget
        self.other = tk.StringVar(value='')
        ttk.Label(frame, text=f'Other {what}:').grid(row=3, column=0, sticky='w', padx=(0, 6), pady=2)
        self.other_entry = ttk.Entry(frame, textvariable=self.other)
        self.other_entry.grid(row=3, column=1, columnspan=2, sticky='ew', pady=2)
        ttk.Label(frame, text=hint, wraplength=1050, foreground='gray25').grid(row=4, column=0, columnspan=3,
                                                                              sticky='w')
        buttons = ttk.Frame(frame)
        buttons.grid(row=5, column=0, columnspan=3, sticky='w', pady=(4, 0))
        self.set_button = ttk.Button(buttons, text='Set the zone', command=self.set_zone)
        self.set_button.pack(side='left')
        self.remove_button = ttk.Button(buttons, text='Remove the selected zones', command=self.remove_zones)
        self.remove_button.pack(side='left', padx=6)
        self.clear_button = ttk.Button(buttons, text='Clear the fields', command=self.clear_fields)
        self.clear_button.pack(side='left')

    def rows(self) -> List[Tuple[str, str]]:
        """The rows of the table: (zone, text of its arguments)."""
        return [tuple(str(value) for value in self.tree.item(item, 'values')) for item in self.tree.get_children()]

    def set_rows(self, rows) -> None:
        _set_rows(self.tree, rows)

    def values(self) -> Dict[str, str]:
        """The values of the fields that are enabled."""
        return {argument: variable.get() for argument, variable in self.vars.items() if argument not in self._disabled}

    def _selected(self) -> None:
        """Fill the fields with the arguments of the selected row."""
        selection = self.tree.selection()
        if not selection:
            return
        zone, text = (str(value) for value in self.tree.item(selection[0], 'values'))
        self.zone.set(zone)
        try:
            fields, other = self.split(text, zone)
        except forms.FormError:
            fields, other = {}, text
        for argument, variable in self.vars.items():
            variable.set(fields.get(argument, ''))
        self.other.set(other)

    def set_zone(self) -> bool:
        """Add the zone of the fields to the table, or replace its arguments."""
        zone = self.zone.get().strip()
        try:
            if not zone:
                raise forms.FormError(f'{self.name}: choose or enter the zone.')
            text = self.compose(self.values(), self.other.get(), zone)
        except forms.FormError as error:
            self.app.show_error(self.title, str(error))
            return False
        for item in self.tree.get_children():
            if str(self.tree.item(item, 'values')[0]).upper() == zone.upper():
                self.tree.item(item, values=(zone, text))
                return True
        self.tree.insert('', 'end', values=(zone, text))
        return True

    def remove_zones(self) -> None:
        for item in self.tree.selection():
            self.tree.delete(item)

    def clear_fields(self) -> None:
        for variable in self.vars.values():
            variable.set('')
        self.other.set('')

    def set_zones(self, zones: List[str]) -> None:
        """The occupied zones, as the choices of the field of the zone."""
        self.zone_combo.configure(values=list(zones))
        if zones and not self.zone.get():
            self.zone.set(zones[0])

    def set_state(self, enabled: bool, disabled: Iterable[str] = ()) -> None:
        """Enable the table and its fields (except those of ``disabled``, which are not given), or disable them. The
        zone and the fields with choices can also be typed, so they are not read-only."""
        self._disabled = set(disabled) if enabled else set(self.fields)
        for argument, widget in self.fields.items():
            on = argument not in self._disabled
            if isinstance(widget, ttk.Combobox):
                widget.configure(state='normal' if on else 'disabled')
            else:
                widget.state(['!disabled'] if on else ['disabled'])
        self.zone_combo.configure(state='normal' if enabled else 'disabled')
        _set_state([self.find_button, self.other_entry, self.set_button, self.remove_button, self.clear_button],
                   enabled)


class _TextWindow:
    """A window with a text that can be saved in a file (the EMS code of the setpoints)."""

    def __init__(self, app: 'AccimApp', title: str, text: str, folder: str, filename: str):
        self.app = app
        self.content, self.folder, self.filename = text, folder, filename
        self.window = tk.Toplevel(app.root)
        self.window.title(title)
        self.window.geometry('1000x700')
        buttons = ttk.Frame(self.window, padding=6)
        buttons.pack(side='bottom', fill='x')
        ttk.Button(buttons, text='Save as...', command=self.save).pack(side='left')
        ttk.Button(buttons, text='Close', command=self.window.destroy).pack(side='right')
        frame = ttk.Frame(self.window)
        frame.pack(fill='both', expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        self.text = tk.Text(frame, wrap='none', font=('Consolas', 9))
        vertical = ttk.Scrollbar(frame, orient='vertical', command=self.text.yview)
        horizontal = ttk.Scrollbar(frame, orient='horizontal', command=self.text.xview)
        self.text.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.text.grid(row=0, column=0, sticky='nsew')
        vertical.grid(row=0, column=1, sticky='ns')
        horizontal.grid(row=1, column=0, sticky='ew')
        self.text.insert('1.0', text)
        self.text.configure(state='disabled')

    def save(self, path: Optional[str] = None) -> bool:
        """Save the text in a file (chosen in a dialog if ``path`` is None)."""
        if path is None:
            path = filedialog.asksaveasfilename(parent=self.window, defaultextension='.txt', initialdir=self.folder,
                                                initialfile=self.filename,
                                                filetypes=[('Text files', '*.txt'), ('All files', '*.*')])
            if not path:
                return False
        with open(path, 'w', encoding='utf-8') as file:
            file.write(self.content)
        self.app.log_text(f'\nThe text has been saved in {path}\n')
        return True


class AddAccisTab(_Tab):
    """Add the ACCIS to the IDF files of a folder (:class:`accim.sim.accis.AddAccis`)."""

    def __init__(self, app: 'AccimApp'):
        super().__init__(app, '1. Add the ACCIS', scrollable=True, bar=True)
        defaults = forms.ADD_ACCIS_DEFAULTS
        body = self.body
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        self.vars: Dict[str, tk.Variable] = {}
        for name in ('script_type', 'supply_air_temp_input_method', 'vrf_availability_schedule', 'vrf_eer', 'vrf_cop',
                     'setpoint_type', 'energyplus_version', 'output_type', 'category', 'comfort_mode',
                     'category_cooling_offset', 'category_heating_offset', 'setpoint_accuracy',
                     'cooling_season_start', 'cooling_season_end',
                     'ventilation_setpoint_offset', 'min_outdoor_temp_offset', 'max_wind_speed',
                     'opening_factor_max_temp_diff', 'opening_factor_min_temp_diff', 'min_opening_factor',
                     'setpoint_tolerance_start', 'setpoint_tolerance_end', 'setpoint_tolerance_step', 'name_suffix',
                     *forms.CUSTOM_MODEL_FIELDS, 'custom_outdoor_metric', *forms.CUSTOM_OUTDOOR_METRIC_FIELDS, 'epw',
                     'custom_regimes', *forms.SETPOINT_LIMIT_FIELDS, 'report_hours_below'):
            self.vars[name] = tk.StringVar(value=defaults[name])
        for name in ('keep_existing_outputs', 'add_building_averages', 'debug_ems', *forms.EXISTING_HVAC_OPTIONS):
            self.vars[name] = tk.BooleanVar(value=defaults[name])
        self.vars['existing_hvac_availability_schedule'] = tk.StringVar(
            value=defaults['existing_hvac_availability_schedule'])
        self.frequencies = {f: tk.BooleanVar(value=f in defaults['output_frequencies'])
                            for f in forms.OUTPUT_FREQUENCIES}
        self.hvac_modes = {m: tk.BooleanVar(value=m in defaults['hvac_mode']) for m in forms.HVAC_MODES}
        self.ventilation_controls = {c: tk.BooleanVar(value=c in defaults['ventilation_control'])
                                     for c in forms.VENTILATION_CONTROLS}
        self.standards = forms.comfort_standard_choices()
        #: The window of the last EMS code of the setpoints shown
        self.ems_code_window: Optional[_TextWindow] = None

        self._folder_row(0, 'Working folder (input IDFs):', refresh=True)
        self._idf_frame(body).grid(row=1, column=0, columnspan=2, sticky='ew', pady=4)
        self._model_frame(body).grid(row=2, column=0, sticky='nsew', padx=(0, 6), pady=4)
        self._comfort_frame(body).grid(row=2, column=1, sticky='nsew', pady=4)
        self.zone_frame = self._zone_frame(body)
        self.zone_frame.grid(row=3, column=0, columnspan=2, sticky='ew', pady=4)
        self._mixed_mode_frame(body).grid(row=4, column=0, sticky='nsew', padx=(0, 6), pady=4)
        self._custom_frame(body).grid(row=4, column=1, sticky='nsew', pady=4)
        self._existing_hvac_frame(body).grid(row=5, column=0, columnspan=2, sticky='ew', pady=4)
        self._setpoint_limits_frame(body).grid(row=6, column=0, columnspan=2, sticky='ew', pady=4)
        self._tolerance_frame(body).grid(row=7, column=0, columnspan=2, sticky='ew', pady=4)
        ttk.Button(self.bar, text='Preview', command=self.preview).pack(side='left')
        self.ems_code_button = ttk.Button(self.bar, text='EMS code of the setpoints...', command=self.show_ems_code)
        self.ems_code_button.pack(side='left', padx=(6, 0))
        self.add_button = ttk.Button(self.bar, text='Add the ACCIS', command=self.add)
        self.add_button.pack(side='left', padx=6)
        self.count = tk.StringVar(value='')
        ttk.Label(self.bar, textvariable=self.count).pack(side='left', padx=6)
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
        ttk.Label(frame, text='Availability schedule of the VRF systems:').grid(row=3, column=0, sticky='w',
                                                                                 padx=(0, 6), pady=2)
        # Any schedule of the model can be typed, so the field is not read-only
        self.vrf_schedule_combo = ttk.Combobox(frame, textvariable=self.vars['vrf_availability_schedule'],
                                               values=list(forms.VRF_AVAILABILITY), width=24)
        self.vrf_schedule_combo.grid(row=3, column=1, sticky='ew', pady=2)
        efficiency = ttk.Frame(frame)
        efficiency.grid(row=4, column=1, sticky='w')
        ttk.Label(frame, text='Efficiency of the VRF systems:').grid(row=4, column=0, sticky='w', padx=(0, 6), pady=2)
        self.vrf_widgets = [_grid_entry(efficiency, 0, 'EER', self.vars['vrf_eer'], width=6),
                            _grid_entry(efficiency, 0, 'COP', self.vars['vrf_cop'], width=6, column=2)]
        efficiency.columnconfigure(2, pad=12)
        _grid_combo(frame, 5, 'Setpoint type:', self.vars['setpoint_type'], forms.SETPOINT_TYPES)
        _grid_combo(frame, 6, 'EnergyPlus version:', self.vars['energyplus_version'], forms.ENERGYPLUS_VERSIONS)
        _grid_combo(frame, 7, 'Outputs:', self.vars['output_type'], forms.OUTPUT_TYPES)
        ttk.Label(frame, text='Output frequencies:').grid(row=8, column=0, sticky='nw', pady=2)
        checks = ttk.Frame(frame)
        checks.grid(row=8, column=1, sticky='w')
        for column, (frequency, variable) in enumerate(self.frequencies.items()):
            ttk.Checkbutton(checks, text=frequency, variable=variable).grid(row=column // 3, column=column % 3,
                                                                           sticky='w', padx=(0, 6))
        ttk.Checkbutton(frame, text='Keep the outputs of the input IDFs',
                        variable=self.vars['keep_existing_outputs']).grid(row=9, column=0, columnspan=2, sticky='w')
        ttk.Checkbutton(frame, text='Building averages of the hour counters (add_building_averages)',
                        variable=self.vars['add_building_averages']).grid(row=10, column=0, columnspan=2, sticky='w')
        ttk.Checkbutton(frame, text='EDD file of the EMS, to check its programs (debug_ems)',
                        variable=self.vars['debug_ems']).grid(row=11, column=0, columnspan=2, sticky='w')
        return frame

    def _comfort_frame(self, parent) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text='Comfort models (adaptive setpoints)', padding=6)
        frame.columnconfigure(1, weight=1)
        self.comfort_widgets: List[Any] = []
        header = ttk.Frame(frame)
        header.grid(row=0, column=0, columnspan=2, sticky='ew', pady=2)
        ttk.Label(header, text='Comfort standards (select one or more):').pack(side='left')
        self.zone_button = ttk.Button(header, text='Other values for some zones...',
                                      command=lambda: self.scroll.see(self.zone_frame))
        self.zone_button.pack(side='right')
        self.comfort_widgets.append(self.zone_button)
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
        self.comfort_widgets.append(_grid_entry(frame, 8, 'Offset of the category, cooling (°C):',
                                                self.vars['category_cooling_offset']))
        self.comfort_widgets.append(_grid_entry(frame, 9, 'heating (°C):', self.vars['category_heating_offset']))
        self.comfort_widgets.append(_grid_entry(frame, 10, 'Accuracy of the setpoints (2: half degrees; 10000: none):',
                                                self.vars['setpoint_accuracy']))
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
        fields = list(forms.CUSTOM_MODEL_FIELDS.items())
        self.custom_widgets = [_grid_entry(frame, row, f'{label}:', self.vars[name])
                               for row, (name, (label, _)) in enumerate(fields)]
        # The outdoor metric of the custom model (accim.sim.ems.outdoor_metric)
        row = len(fields)
        self.metric_combo = _grid_combo(frame, row, 'Outdoor metric (custom_outdoor_metric):',
                                        self.vars['custom_outdoor_metric'], forms.CUSTOM_OUTDOOR_METRICS)
        self.custom_widgets.append(self.metric_combo)
        self.metric_description = ttk.Label(frame, text='', wraplength=340)
        self.metric_description.grid(row=row + 1, column=0, columnspan=2, sticky='w', pady=(0, 2))
        self.vars['custom_outdoor_metric'].trace_add('write', lambda *args: self._metric_changed())
        row += 2
        for name, (label, _) in forms.CUSTOM_OUTDOOR_METRIC_FIELDS.items():
            self.custom_widgets.append(_grid_entry(frame, row, f'{label}:', self.vars[name]))
            row += 1
        ttk.Label(frame, text='Weather file of the simulations (epw),\nwith which the outdoor metric begins:').grid(
            row=row, column=0, sticky='w', padx=(0, 6), pady=2)
        epw_frame = ttk.Frame(frame)
        epw_frame.grid(row=row, column=1, sticky='ew', pady=2)
        epw_frame.columnconfigure(0, weight=1)
        self.epw_entry = ttk.Entry(epw_frame, textvariable=self.vars['epw'])
        self.epw_entry.grid(row=0, column=0, sticky='ew')
        self.epw_button = ttk.Button(epw_frame, text='Browse...', command=self.choose_epw)
        self.epw_button.grid(row=0, column=1, padx=(4, 0))
        self.custom_widgets += [self.epw_entry, self.epw_button]
        # The regimes of the custom model (accim.sim.ems.custom_regimes)
        row += 1
        self.custom_widgets.append(_grid_entry(frame, row, 'Regimes (custom_regimes):', self.vars['custom_regimes']))
        ttk.Label(frame, text=forms.CUSTOM_REGIMES_HINT, wraplength=340, foreground='gray25').grid(
            row=row + 1, column=0, columnspan=2, sticky='w', pady=(0, 2))
        self._metric_changed()
        return frame

    def _metric_changed(self) -> None:
        """The description of the outdoor metric of the custom model."""
        self.metric_description.configure(
            text=forms.CUSTOM_OUTDOOR_METRICS.get(self.vars['custom_outdoor_metric'].get(), ''))

    def choose_epw(self) -> bool:
        """Choose the weather file of the simulations (the outdoor metric of the custom model begins with it)."""
        path = filedialog.askopenfilename(parent=self.app.root, initialdir=self.folder.get() or None,
                                          filetypes=[('EPW files', '*.epw'), ('All files', '*.*')],
                                          title='The weather file of the simulations')
        if not path:
            return False
        self.vars['epw'].set(path)
        return True

    def _existing_hvac_frame(self, parent) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text='Existing HVAC systems (script types ex_ac and ex_mm): keep the operative '
                                            'temperature between the setpoints', padding=6)
        (self.existing_hvac_widgets, self.existing_hvac_temperature_widgets,
         self.availability_combo) = _existing_hvac_widgets(frame, self.vars)
        return frame

    def _setpoint_limits_frame(self, parent) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text='Floor and ceiling of the setpoints (setpoint type temperature), and '
                                            'occupied hours below some temperatures', padding=6)
        # The values of Table B.2 of EN 16798-1 fill both fields (accim.constants.EN16798_TABLE_B2)
        self.table_b2 = tk.StringVar(value='')
        self.table_b2_combo = _grid_combo(frame, 0, 'EN 16798-1, Table B.2 (fills the floor and ceiling):',
                                          self.table_b2, ('', *forms.EN16798_TABLE_B2_CHOICES), width=34)
        self.table_b2.trace_add('write', lambda *args: self._table_b2_chosen())
        self.limit_widgets: List[Any] = [self.table_b2_combo]
        for row, (name, (label, _)) in enumerate(forms.SETPOINT_LIMIT_FIELDS.items(), start=1):
            self.limit_widgets.append(_grid_entry(frame, row, f'{label}:', self.vars[name], width=8))
        _grid_entry(frame, 3, 'Occupied hours below (°C, such as 18 17 16; empty: none):',
                    self.vars['report_hours_below'], width=8)
        ttk.Label(frame, text='The heating setpoint is not lower than the floor, and the cooling setpoint not higher '
                              'than the ceiling, whatever the comfort standard and comfort mode (the cooling '
                              'setpoint is rounded down, below the ceiling). The PMV-based setpoints have neither.',
                  wraplength=760, foreground='gray25').grid(row=4, column=0, columnspan=2, sticky='w', pady=(2, 0))
        return frame

    def _table_b2_chosen(self) -> None:
        """Fill the floor and ceiling of the setpoints with the values of Table B.2 of EN 16798-1 chosen."""
        values = forms.EN16798_TABLE_B2_CHOICES.get(self.table_b2.get())
        if values is not None:
            for name, value in zip(forms.SETPOINT_LIMIT_FIELDS, values):
                self.vars[name].set(str(value))

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
        frame = ttk.LabelFrame(parent, text='Arguments of each zone (zone_arguments): other comfort standards, '
                                            'categories, comfort modes... for some zones; the other zones have those '
                                            'of the form', padding=6)
        fields = [('comfort_standard', 'Comfort standard:', forms.zone_field_choices('comfort_standard')),
                  ('hvac_mode', 'HVAC mode (mixed mode):', forms.zone_field_choices('hvac_mode')),
                  ('category', 'Category:', forms.zone_field_choices('category')),
                  ('ventilation_control', 'Ventilation control (mixed mode):',
                   forms.zone_field_choices('ventilation_control')),
                  ('comfort_mode', 'Comfort mode:', forms.zone_field_choices('comfort_mode'))]
        hint = ('Empty fields take the values of each output IDF: with another comfort standard, give its category '
                'and comfort mode too (the lists show those of the comfort standard of the zone). Other arguments: '
                'pairs name=value separated by commas, for instance setpoint_tolerance=0.25, '
                'cooling_season_start=01/06; the arguments of a zone are ' + ', '.join(forms.ZONE_ARGUMENTS)
                + '. Preview checks that each zone has setpoints in all the output IDFs.')
        self.zone_table = _ZoneTable(self.app, frame, fields, forms.zone_row_text, forms.split_zone_arguments,
                                     self.find_zones, 'Arguments of a zone', 'zone_arguments', hint)
        self.zone_table.vars['comfort_standard'].trace_add('write', lambda *args: self._zone_standard_changed())
        # The names of the table of the zones of earlier versions of the window
        self.zone_tree = self.zone_table.tree
        self.zone_name = self.zone_table.zone
        self.zone_text = self.zone_table.other
        self.zone_combo = self.zone_table.zone_combo
        return frame

    def _zone_standard_changed(self) -> None:
        """The categories and comfort modes of the comfort standard of the zone, as the choices of their fields."""
        standard = self.zone_table.vars['comfort_standard'].get()
        for name in ('category', 'comfort_mode'):
            self.zone_table.fields[name].configure(values=forms.zone_field_choices(name, standard))

    def selected_standards(self) -> List[int]:
        return [self.standards[index][0] for index in self.standard_list.curselection()]

    def refresh_idfs(self) -> None:
        """List the input IDFs of the folder, all selected."""
        _fill_list(self.idf_list, forms.input_idfs(self.folder.get()))

    def update_state(self) -> None:
        """Enable the fields that apply to the script type, the setpoint type and the comfort standards."""
        script_type = self.vars['script_type'].get()
        self.script_description.configure(text=forms.SCRIPT_TYPES.get(script_type, ''))
        vrf = script_type.startswith('vrf')
        mixed_mode = script_type in forms.MIXED_MODE_SCRIPT_TYPES
        _set_state([self.supply_air, *self.vrf_widgets], vrf)
        # Any schedule of the model can be typed, so the field is not read-only
        self.vrf_schedule_combo.configure(state='normal' if vrf else 'disabled')
        _set_state(self.mixed_mode_widgets, mixed_mode)
        temperature = self.vars['setpoint_type'].get() == 'temperature'
        _set_existing_hvac_state(self.existing_hvac_widgets, self.existing_hvac_temperature_widgets,
                                 self.availability_combo, script_type.startswith('ex'), temperature)
        _set_state(self.comfort_widgets, temperature)
        _set_state([self.ems_code_button], temperature)
        # The PMV-based setpoints have neither floor nor ceiling (decision D5 of accim 1.2.0)
        _set_state(self.limit_widgets, temperature)
        self.zone_table.set_state(temperature, () if mixed_mode else ('hvac_mode', 'ventilation_control'))
        standards = self.selected_standards() if temperature else []
        _set_state(self.custom_widgets, 99 in standards)
        self.categories.configure(text=forms.categories_hint(standards))
        self.comfort_modes.configure(text=forms.comfort_modes_hint(standards))

    def zone_rows(self) -> List[Tuple[str, str]]:
        """The rows of the table of the zones: (zone, text of its arguments)."""
        return self.zone_table.rows()

    def set_zone(self) -> bool:
        """Add the zone of the fields to the table, or replace its arguments."""
        return self.zone_table.set_zone()

    def remove_zones(self) -> None:
        self.zone_table.remove_zones()

    def find_zones(self) -> bool:
        """List the occupied zones of the first selected input IDF in the field of the zone (in a thread)."""
        idfs = _selected(self.idf_list)
        if not idfs:
            self.app.show_error('Find the occupied zones', 'Select an input IDF first.')
            return False
        version = self.vars['energyplus_version'].get()

        def done(zones):
            self.zone_table.set_zones(zones)
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
        if values['setpoint_type'] != 'temperature':
            # The fields of the floor and ceiling of the setpoints, and of the regimes of the custom model, are
            # disabled
            values.update(dict.fromkeys(forms.SETPOINT_LIMIT_FIELDS, ''), custom_regimes='')
        return values

    def state(self) -> Dict[str, Any]:
        state = super().state()
        state.update(
            idfs=_selected(self.idf_list),
            output_frequencies=_checks_state(self.frequencies),
            comfort_standard=self.selected_standards(),
            hvac_mode=_checks_state(self.hvac_modes),
            ventilation_control=_checks_state(self.ventilation_controls),
            zone_arguments=self.zone_rows(),
        )
        return state

    def restore(self, state: Mapping[str, Any]) -> List[str]:
        messages = super().restore(state)
        if 'idfs' in state:
            messages += _select(self.idf_list, state['idfs'], 'Input IDFs of "1. Add the ACCIS"')
        for name, checks in (('output_frequencies', self.frequencies), ('hvac_mode', self.hvac_modes),
                             ('ventilation_control', self.ventilation_controls)):
            if name in state:
                _restore_checks(checks, state[name])
        if 'comfort_standard' in state:
            # A disabled list (with PMV setpoints) does not change its selection
            self.standard_list.configure(state='normal')
            self.standard_list.selection_clear(0, 'end')
            for index, (number, _) in enumerate(self.standards):
                if number in state['comfort_standard']:
                    self.standard_list.selection_set(index)
        if 'zone_arguments' in state:
            _set_rows(self.zone_tree, state['zone_arguments'])
        self.update_state()
        return messages

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
                          + ''.join(f'    {name} = {value!r}\n' for name, value in arguments.items())
                          + 'Add the ACCIS shows the estimated size of the results of their simulations before '
                            'writing them.\n')

    def add(self) -> bool:
        """Add the ACCIS to the selected IDFs, in the folder (in a thread): AddAccis prepares the models and prints the
        estimated size of the results of the output IDFs, and the window asks whether to write them."""
        arguments = self._arguments()
        if arguments is None:
            return False
        total = arguments.pop('_total')
        if total == 0:
            self.app.show_error('Add the ACCIS', 'These arguments give no output IDF: check the comfort standards, '
                                                 'categories and comfort modes.')
            return False
        folder = self.folder.get()
        # AddAccis asks before writing the output IDFs, after printing the estimated size of their results
        arguments['confirm'] = None

        def confirm(question: str, printed: str) -> str:
            return 'y' if self.app.ask_from_task('Add the ACCIS', _write_question(printed, folder, total)) else 'n'

        def task():
            from accim.sim.accis import AddAccis

            return len(AddAccis(**arguments).output_idfs)

        def done(written):
            self.app.folder_changed()
            if written:
                self.app.show_info('Add the ACCIS', f'{written} output IDFs have been written.')
            else:
                self.app.log_text('No output IDF has been written.\n')

        return self.app.run_task('Add the ACCIS', folder, task, on_done=done, answers={ADD_ACCIS_QUESTION: confirm})

    def show_ems_code(self) -> bool:
        """Show the EMS code with which the ACCIS calculates the setpoints of the comfort standards, categories and
        comfort modes of the form, and of the zones of the table with other comfort standards, in a window (the code
        is made in a thread)."""
        try:
            calls = forms.setpoint_ems_code_calls(self.form())
        except forms.FormError as error:
            self.app.show_error('EMS code of the setpoints', str(error))
            return False
        folder = self.folder.get() if os.path.isdir(self.folder.get()) else os.getcwd()

        def done(text):
            self.ems_code_window = _TextWindow(self.app, 'EMS code of the setpoints', text, folder,
                                               'accim_setpoint_ems_code.txt')

        return self.app.run_task('EMS code of the setpoints', folder, lambda: tasks.setpoint_ems_code(calls),
                                 on_done=done)


class ApmvTab(_Tab):
    """Apply the setpoints based on the predicted mean vote (PMV) or an index derived from it (aPMV, ePMV) to an IDF of
    the folder (:mod:`accim.sim.apmv`)."""

    def __init__(self, app: 'AccimApp'):
        super().__init__(app, '2. PMV-based setpoints', scrollable=True, bar=True)
        defaults = forms.APMV_DEFAULTS
        body = self.body
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        self.vars: Dict[str, tk.Variable] = {}
        for name in ('idf', 'output_idf', 'energyplus_version', 'supply_air_temp_input_method', 'index',
                     'adaptive_coefficients', *forms.APMV_OPTIONS, *forms.APMV_SETPOINT_FIELDS,
                     'cooling_season_start', 'cooling_season_end', *forms.PMV_INPUT_FIELDS):
            self.vars[name] = tk.StringVar(value=defaults[name])
        for name in ('add_vrf_system', 'always_occupied', 'other_pmv_related_outputs', *forms.EPMV_OPTIONS):
            self.vars[name] = tk.BooleanVar(value=defaults[name])
        self.frequencies = {f: tk.BooleanVar(value=f in defaults['output_frequencies'])
                            for f in forms.OUTPUT_FREQUENCIES}
        self._folder_row(0, 'Working folder (input IDFs):', refresh=True)

        model = ttk.LabelFrame(body, text='Model', padding=6)
        model.grid(row=1, column=0, sticky='nsew', padx=(0, 6), pady=4)
        model.columnconfigure(1, weight=1)
        self.idf_combo = _grid_combo(model, 0, 'Input IDF:', self.vars['idf'], [])
        _grid_entry(model, 1, 'Output IDF (empty: <input>_<index>.idf):', self.vars['output_idf'])
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

        setpoints = ttk.LabelFrame(body, text='Setpoints (of all the zones, except those of the table below)',
                                   padding=6)
        setpoints.grid(row=1, column=1, sticky='nsew', pady=4)
        setpoints.columnconfigure(1, weight=1)
        self.index_combo = _grid_combo(setpoints, 0, 'Index (aPMV, ePMV or PMV):', self.vars['index'],
                                       forms.PMV_INDEX_FUNCTIONS, width=10)
        self.index_combo.bind('<<ComboboxSelected>>', lambda event: self.update_state())
        self.setpoint_entries = {name: _grid_entry(setpoints, row, f'{label}:', self.vars[name], width=10)
                                 for row, (name, label) in enumerate(forms.APMV_SETPOINT_FIELDS.items(), start=1)}
        row = len(forms.APMV_SETPOINT_FIELDS) + 1
        # The adaptive coefficients of the literature (accim.constants.APMV_ADAPTIVE_COEFFICIENTS), which fill the
        # fields of the coefficients, and how the coefficient of each timestep is chosen
        self.coefficients_combo = _grid_combo(setpoints, row, 'λ of the literature (aPMV):',
                                              self.vars['adaptive_coefficients'],
                                              forms.adaptive_coefficient_choices(), width=32)
        self.coefficients_combo.bind('<<ComboboxSelected>>', lambda event: self.fill_coefficients())
        self.coefficients_note = ttk.Label(setpoints, text='', foreground='gray25', wraplength=420)
        self.coefficients_note.grid(row=row + 1, column=0, columnspan=2, sticky='w')
        self.apmv_combos = [self.coefficients_combo]
        row += 2
        for name, label in forms.APMV_OPTIONS.items():
            self.apmv_combos.append(_grid_combo(setpoints, row, label, self.vars[name],
                                                forms.ADAPTIVE_COEFFICIENT_BY, width=10))
            row += 1
        self.epmv_checks = []
        for name, label in forms.EPMV_OPTIONS.items():
            check = ttk.Checkbutton(setpoints, text=label, variable=self.vars[name])
            check.grid(row=row, column=0, columnspan=2, sticky='w')
            self.epmv_checks.append(check)
            row += 1
        _grid_entry(setpoints, row, 'Cooling season from (dd/mm or day):', self.vars['cooling_season_start'],
                    width=10)
        _grid_entry(setpoints, row + 1, 'to (dd/mm or day):', self.vars['cooling_season_end'], width=10)

        pmv = ttk.LabelFrame(body, text='Inputs of the PMV of the occupants (empty: those of the model)', padding=6)
        pmv.grid(row=2, column=0, columnspan=2, sticky='ew', pady=4)
        for index, (name, label) in enumerate(forms.PMV_INPUT_FIELDS.items()):
            _grid_entry(pmv, index // 2, f'{label}:', self.vars[name], width=10, column=(index % 2) * 2)
        pmv.columnconfigure(2, pad=24)

        zones = ttk.LabelFrame(body, text='Setpoints of each zone: other setpoints for some zones', padding=6)
        zones.grid(row=3, column=0, columnspan=2, sticky='ew', pady=4)
        tolerances = [name for name in forms.APMV_SETPOINT_FIELDS if name not in forms.APMV_ZONE_FIELDS]
        hint = ('Empty fields take the values above. Other setpoints: pairs name=value separated by commas, such as '
                'cooling_setpoint_tolerance_cooling_season=-0.2 (' + ', '.join(tolerances) + '). The zones are the '
                'occupied zones of the input IDF.')
        self.zone_table = _ZoneTable(
            self.app, zones, [(name, f'{forms.APMV_SETPOINT_FIELDS[name]}:', None) for name in forms.APMV_ZONE_FIELDS],
            forms.apmv_zone_row_text, forms.split_apmv_zone_setpoints, self.find_zones, 'Setpoints of a zone',
            'zone_setpoints', hint, what='setpoints')

        ttk.Button(self.bar, text='Apply the setpoints', command=self.apply).pack(side='left')
        ttk.Label(body, text='The thermostats keep an index of the comfort of each zone between the heating and cooling '
                             'setpoints (section 4.8 of the documentation): the aPMV, which corrects the PMV for the '
                             'adaptation of the occupants, aPMV = PMV / (1 + λ·PMV), with one λ for the cooling season '
                             'and another for the heating season (or, with "pmv_sign", one for warm sensations and '
                             'another for cool ones; "λ of the literature" fills them with those of Yao et al. 2009, '
                             'the Chinese standard GB/T 50785 or Zhang et al. 2024); the ePMV of Fanger and Toftum, '
                             'ePMV = e·PMV, with the '
                             'expectancy factor e (0.5 to 1) of buildings without air-conditioning in warm climates, '
                             'in the cooling season and on the warm side of the scale; or the PMV. To simulate the new '
                             'IDF in the tab "4. Run the simulations", uncheck "Only the output IDFs of accim".',
                  foreground='gray25', wraplength=900).grid(row=4, column=0, columnspan=2, sticky='w')
        self.update_state()

    def refresh(self) -> None:
        """List the input IDFs of the folder."""
        idfs = forms.input_idfs(self.folder.get())
        self.idf_combo.configure(values=idfs)
        if self.vars['idf'].get() not in idfs:
            self.vars['idf'].set(idfs[0] if idfs else '')

    def update_state(self) -> None:
        """Enable the fields of the index of the setpoints only (and the supply air temperature with the VRF systems)."""
        _set_state([self.supply_air], self.vars['add_vrf_system'].get())
        index = self.vars['index'].get()
        others = {name for key, names in forms.PMV_INDEX_PARAMETERS.items() if key != index for name in names}
        for name, entry in self.setpoint_entries.items():
            _set_state([entry], name not in others)
        _set_state(self.epmv_checks, index == 'epmv')
        _set_state(self.apmv_combos, index == 'apmv')
        self.zone_table.set_state(True, disabled=[name for name in forms.APMV_ZONE_FIELDS if name in others])

    def fill_coefficients(self) -> None:
        """Write the adaptive coefficients of the chosen entry of the catalogue in their fields, and describe it."""
        try:
            cooling, heating, description = forms.adaptive_coefficient_entry(self.vars['adaptive_coefficients'].get())
        except forms.FormError as error:
            self.app.show_error('PMV-based setpoints', str(error))
            return
        if cooling:
            self.vars['adaptive_coefficient_cooling'].set(cooling)
        if heating:
            self.vars['adaptive_coefficient_heating'].set(heating)
        self.coefficients_note.configure(text=description)

    def form(self) -> Dict[str, Any]:
        """The values of the form, for :func:`accim.gui.forms.apmv_arguments`."""
        values: Dict[str, Any] = {name: variable.get() for name, variable in self.vars.items()}
        values.update(folder=self.folder.get(),
                      output_frequencies=[f for f, variable in self.frequencies.items() if variable.get()],
                      zone_setpoints=self.zone_table.rows())
        return values

    def find_zones(self) -> bool:
        """List the occupied zones of the input IDF in the field of the zone (in a thread)."""
        idf = self.vars['idf'].get()
        if not idf:
            self.app.show_error('Find the occupied zones', 'Choose the input IDF first.')
            return False
        version = self.vars['energyplus_version'].get()

        def done(zones):
            self.zone_table.set_zones(zones)
            self.app.log_text(f'The occupied zones of {idf} are: {", ".join(zones)}\n')

        return self.app.run_task('Find the occupied zones', self.folder.get(),
                                 lambda: tasks.occupied_zones(idf, version), on_done=done)

    def state(self) -> Dict[str, Any]:
        return dict(super().state(), output_frequencies=_checks_state(self.frequencies),
                    zone_setpoints=self.zone_table.rows())

    def restore(self, state: Mapping[str, Any]) -> List[str]:
        messages = super().restore(state)
        messages += _file_messages(self.vars['idf'].get(), forms.input_idfs(self.folder.get()),
                                   'Input IDF of "2. PMV-based setpoints"')
        if 'output_frequencies' in state:
            _restore_checks(self.frequencies, state['output_frequencies'])
        if 'zone_setpoints' in state:
            self.zone_table.set_rows(state['zone_setpoints'])
        try:
            self.coefficients_note.configure(
                text=forms.adaptive_coefficient_entry(self.vars['adaptive_coefficients'].get())[2])
        except forms.FormError:
            self.vars['adaptive_coefficients'].set('')
            self.coefficients_note.configure(text='')
        self.update_state()
        return messages

    def apply(self) -> bool:
        """Apply the setpoints of the index to the input IDF and save it with the new name (in a thread)."""
        try:
            arguments = forms.apmv_arguments(self.form())
        except forms.FormError as error:
            self.app.show_error('PMV-based setpoints', str(error))
            return False
        name = forms.PMV_INDEX_NAMES[arguments['index']]
        question = f'Apply the {name} setpoints to {arguments["idf"]} and save it as {arguments["output_idf"]}?'
        if os.path.exists(os.path.join(self.folder.get(), arguments['output_idf'])):
            question += f' {arguments["output_idf"]} will be overwritten.'
        if not self.app.ask_yes_no('PMV-based setpoints', question):
            return False

        def done(written):
            self.app.folder_changed()
            self.app.show_info('PMV-based setpoints', f'{written} has been written.')

        return self.app.run_task(f'{name} setpoints', self.folder.get(), lambda: tasks.apply_apmv(arguments),
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

    def state(self) -> Dict[str, Any]:
        return dict(epws=_selected(self.epw_list), cities=self.cities.get('1.0', 'end-1c'),
                    countries=self.countries.get('1.0', 'end-1c'), delete_originals=self.delete_originals.get())

    def restore(self, state: Mapping[str, Any]) -> List[str]:
        messages = []
        if 'epws' in state:
            messages += _select(self.epw_list, state['epws'], 'EPWs of "3. Rename the EPWs"')
        for name, text in (('cities', self.cities), ('countries', self.countries)):
            if name in state:
                text.delete('1.0', 'end')
                text.insert('1.0', state[name])
        if 'delete_originals' in state:
            self.delete_originals.set(bool(state['delete_originals']))
        return messages

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
            'simulate': tk.BooleanVar(value=defaults['simulate']),
        }
        self._folder_row(0, 'Working folder (IDFs and EPWs):', refresh=True)
        self.only_accim_idfs_check = ttk.Checkbutton(body, text="Only the output IDFs of accim (with '[' in the name)",
                                                     variable=self.vars['only_accim_idfs'], command=self.refresh)
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
        ttk.Button(buttons, text='Estimate the size of the results', command=self.estimate_size).pack(side='left',
                                                                                                     padx=6)
        ttk.Button(buttons, text='Run the simulations', command=self.run).pack(side='left')
        ttk.Button(buttons, text='Remove the simulation files', command=self.remove_files).pack(side='left', padx=6)
        ttk.Checkbutton(body, text='Measure the size of the results in a simulation of an IDF of each group with the '
                                   'same outputs, with the first EPW (slower; otherwise, it is estimated from the '
                                   'outputs of the IDFs in a few seconds)',
                        variable=self.vars['simulate']).grid(row=7, column=0, columnspan=2, sticky='w')
        self.count = tk.StringVar(value='')
        ttk.Label(body, textvariable=self.count).grid(row=8, column=0, columnspan=2, sticky='w', pady=(6, 0))
        self.size = tk.StringVar(value='')
        ttk.Label(body, textvariable=self.size, wraplength=900).grid(row=9, column=0, columnspan=2, sticky='w')
        ttk.Label(body, text='Each simulation is named "IDF name[EPW name"; its CSV files are written in the '
                             'folder. "Remove the simulation files" keeps the IDF, EPW, CSV and ESO files.',
                  foreground='gray25', wraplength=700).grid(row=10, column=0, columnspan=2, sticky='w', pady=(6, 0))

    def form(self) -> Dict[str, Any]:
        """The values of the form, for :func:`accim.gui.forms.run_ep_arguments`."""
        values: Dict[str, Any] = {name: variable.get() for name, variable in self.vars.items()}
        values['folder'] = self.folder.get()
        return values

    def restore(self, state: Mapping[str, Any]) -> List[str]:
        messages = super().restore(state)
        self.refresh()
        return messages

    def preview(self) -> None:
        pairs = forms.simulations(self.folder.get(), self.vars['only_accim_idfs'].get())
        idfs = sorted({idf for idf, _ in pairs})
        epws = sorted({epw for _, epw in pairs})
        self.count.set(f'{len(idfs)} IDFs and {len(epws)} EPWs: {len(pairs)} simulations')

    def refresh(self) -> None:
        """Count the simulations of the folder again, and forget the size of the results of other simulations."""
        self.size.set('')
        self.preview()

    def estimate_size(self) -> bool:
        """Estimate the size of the results of the simulations of the folder (in a thread), as
        :func:`accim.run.estimate_results_size`; it prints the size of each simulation in the log."""
        try:
            arguments = forms.results_size_arguments(self.form())
        except forms.FormError as error:
            self.app.show_error('Size of the results', str(error))
            return False

        def done(result):
            _, sentence = result
            self.size.set(sentence)

        return self.app.run_task('Size of the results', self.folder.get(), lambda: tasks.results_size(arguments),
                                 on_done=done)

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

    #: The text of the tab before the percentages are computed
    EXPLANATION = ('The occupied hours in which the operative temperature is within the setpoints, as a percentage of '
                   'the occupied hours (from the EMS outputs of the hours of accim in the CSV files).')

    def __init__(self, app: 'AccimApp'):
        super().__init__(app, '5. Hours within the setpoints')
        body = self.body
        body.columnconfigure(1, weight=1)
        body.rowconfigure(4, weight=1)
        self.minimum = tk.StringVar(value='90')
        self.zones = tk.StringVar(value='building')
        self.summary = None
        #: The table of hours_within_setpoints shown, with the minimum and the zones (for the session files)
        self.shown: Optional[Dict[str, Any]] = None
        self._folder_row(0, 'Working folder (CSV files of the simulations):')
        _grid_entry(body, 1, 'Minimum percentage of the occupied hours within the setpoints:', self.minimum,
                    width=8).grid(sticky='w')
        zones = _grid_combo(body, 2, 'Reached by (building, all, or the zones separated by commas):', self.zones,
                            ('building', 'all'), width=40)
        # Some zones can be typed, so the field is not read-only
        zones.configure(state='normal')
        zones.grid(sticky='w')
        buttons = ttk.Frame(body)
        buttons.grid(row=3, column=0, columnspan=2, sticky='w', pady=6)
        ttk.Button(buttons, text='Compute', command=self.compute).pack(side='left')
        self.export_button = ttk.Button(buttons, text='Export to CSV...', command=self.export, state='disabled')
        self.export_button.pack(side='left', padx=6)
        self.result = tk.StringVar(value=self.EXPLANATION)
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

    def show(self, summary, minimum: float, zones: Optional[Any] = None) -> None:
        """Show the percentages of each simulation, and which ones reach the minimum in the zones (those of the form
        if None: 'building', 'all' or a list of zones)."""
        from accim.data.postprocessing.setpoint_hours import filter_by_hours_within_setpoints

        try:
            zones = forms.hours_zones(self.zones.get()) if zones is None else zones
            kept = filter_by_hours_within_setpoints(summary, minimum, zones=zones)
        except ValueError as error:
            self.app.show_error('Hours within the setpoints', str(error))
            return
        self.shown = {'summary': summary, 'minimum': minimum, 'zones': zones}
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
        where = zones if isinstance(zones, str) else ', '.join(zones)
        self.result.set(f'{len(kept)} of the {len(summary)} simulations reach {minimum} % of the occupied hours '
                        f'within the setpoints ({where}).')
        self.export_button.state(['!disabled'])

    def clear(self) -> None:
        """Remove the percentages shown."""
        self.summary = self.shown = None
        self.tree.delete(*self.tree.get_children())
        self.tree.configure(columns=())
        self.result.set(self.EXPLANATION)
        self.export_button.state(['disabled'])

    def state(self) -> Dict[str, Any]:
        return dict(minimum=self.minimum.get(), zones=self.zones.get())

    def restore(self, state: Mapping[str, Any], shown: Optional[Mapping[str, Any]] = None) -> List[str]:
        """Set the fields of the tab, and show the percentages of the session (``shown``), if it has them."""
        _restore_variables({'minimum': self.minimum, 'zones': self.zones}, state)
        if shown is None:
            self.clear()
        else:
            self.show(shown['summary'], shown['minimum'], shown['zones'])
        return []

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
        for name in ('standard_outputs', 'split_epw_names', 'long_term_indicators'):
            self.vars[name] = tk.BooleanVar(value=defaults[name])
        self.levels = {level: tk.BooleanVar(value=level in defaults['level']) for level in ('block', 'building')}
        self.level_funcs = {func: tk.BooleanVar(value=func in defaults['level_agg_func']) for func in ('sum', 'mean')}
        self.table = None
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
        ttk.Checkbutton(checks, text='Long-term discomfort indicators (CEN/TR 16798-2; tables of hours or timesteps)',
                        variable=self.vars['long_term_indicators']).pack(side='left')
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
        self.save_button = ttk.Button(buttons, text='Save the table...', command=self.save_table, state='disabled')
        self.save_button.pack(side='left')
        ttk.Button(buttons, text='Open a table...', command=self.open_table).pack(side='left', padx=6)
        self.summary = tk.StringVar(value='')
        ttk.Label(frame, textvariable=self.summary, wraplength=900).grid(row=9, column=0, columnspan=2, sticky='w')
        ttk.Label(frame, text='"Save the table" saves it in a pickle file, which "Open a table" opens again without '
                              'the CSV files (also the tables saved in Python with Table.save), and in a JSON file '
                              'with the same name, to read it.', foreground='gray25', wraplength=900).grid(
            row=10, column=0, columnspan=2, sticky='w')

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
        return self.app.run_task('Table', self.folder.get(), lambda: tasks.make_table(arguments),
                                 on_done=self.show_table)

    def show_table(self, table, source: str = '') -> None:
        """Show the table, and the columns that the figures can use.

        :param source: The file from which the table was opened, if it was.
        """
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
        opened = f'Table of {source} ({getattr(table, "frequency", "")}): ' if source else ''
        self.summary.set(f'{opened}{len(df)} rows{shown} and {len(df.columns)} columns. The variables whose values '
                         f'differ between the simulations: {differing or "none (the figures need at least two)"}.')
        for button in (self.export_button, self.figure_button, self.save_button):
            button.state(['!disabled'])
        indicators = getattr(table, 'long_term_indicators', None)
        if indicators is not None:
            # The indicators of each simulation (Table(long_term_indicators=True)), one column per simulation
            self.app.log_text('\nThe long-term discomfort indicators of CEN/TR 16798-2 (Annex D) of each simulation '
                              '(Table.long_term_indicators):\n'
                              + indicators.set_index('Source').T.to_string() + '\n')

    def clear(self) -> None:
        """Forget the table (when a session without a table is opened)."""
        self.table = None
        self.tree.delete(*self.tree.get_children())
        self.tree.configure(columns=())
        for listbox in (self.rows_list, self.cols_list, self.y_list):
            listbox.delete(0, 'end')
        self.x_combo.configure(values=[])
        for button in (self.export_button, self.figure_button, self.save_button):
            button.state(['disabled'])
        self.refresh()

    def export(self) -> None:
        if self.table is not None:
            _export_dataframe(self.app, self.table.df, self.folder.get(), 'accim_table.csv')

    def save_table(self, path: Optional[str] = None) -> bool:
        """Save the table in a pickle file and a JSON file with the same name (:meth:`Table.save`, in a thread).

        :param path: The path of the pickle file; if None, a dialog asks for it.
        """
        if self.table is None:
            self.app.show_error('Save the table', 'Make the table first.')
            return False
        if path is None:
            path = filedialog.asksaveasfilename(
                parent=self.app.root, defaultextension='.pkl', initialdir=self.folder.get(),
                initialfile='accim_table.pkl', filetypes=TABLE_FILE_TYPES,
                title='Save the table (a pickle file, and a JSON file with the same name to read it)')
            if not path:
                return False
        # The task runs in the folder of the file, so a relative path would be read from there again
        path = os.path.abspath(path)
        table = self.table
        return self.app.run_task('Save the table', _folder_of(path), lambda: tasks.save_table(table, path))

    def open_table(self, path: Optional[str] = None) -> bool:
        """Open a table saved by this tab or in Python with :meth:`Table.save` (in a thread).

        :param path: The path of the pickle file; if None, a dialog asks for it.
        """
        if path is None:
            path = filedialog.askopenfilename(parent=self.app.root, initialdir=self.folder.get(),
                                              filetypes=TABLE_FILE_TYPES,
                                              title='Open a table saved by this tab or with Table.save')
            if not path:
                return False
        path = os.path.abspath(path)
        return self.app.run_task('Open a table', _folder_of(path), lambda: tasks.open_table(path),
                                 on_done=lambda table: self.show_table(table, source=path))

    def state(self) -> Dict[str, Any]:
        state = super().state()
        state.update(
            level=_checks_state(self.levels),
            level_agg_func=_checks_state(self.level_funcs),
            vars_to_gather_rows=_selected(self.rows_list),
            vars_to_gather_cols=_selected(self.cols_list),
            data_on_y_main_axis=_selected(self.y_list),
        )
        return state

    def restore(self, state: Mapping[str, Any], table=None) -> List[str]:
        """Set the fields of the tab, and show the table of the session (``table``), if it has one."""
        messages = super().restore(state)
        messages += _file_messages(self.vars['idf_path'].get(), forms.idf_files(self.folder.get()),
                                   'IDF of "6. Table and figures"')
        for name, checks in (('level', self.levels), ('level_agg_func', self.level_funcs)):
            if name in state:
                _restore_checks(checks, state[name])
        if table is None:
            self.clear()
            return messages
        x_axis = self.vars['data_on_x_axis'].get()
        self.show_table(table)
        for listbox, name in ((self.rows_list, 'vars_to_gather_rows'), (self.cols_list, 'vars_to_gather_cols'),
                              (self.y_list, 'data_on_y_main_axis')):
            messages += _select(listbox, state.get(name, []), f'Columns of the figure of "6. Table and figures" '
                                                                f'({name})')
        if x_axis in self.y_list.get(0, 'end'):
            self.vars['data_on_x_axis'].set(x_axis)
        return messages

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
        table = self.table

        def task():
            # The figures filter the rows of the table: each one starts from the whole table
            table.format_table(**tasks.table_format(table))
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
                         'out_dir', 'existing_hvac_availability_schedule')}
        for name in forms.EXISTING_HVAC_OPTIONS:
            self.vars[name] = tk.BooleanVar(value=defaults[name])
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

        existing = ttk.LabelFrame(body, text='Existing HVAC systems (script type ex_ac): keep the operative temperature '
                                             'between the setpoints', padding=6)
        existing.grid(row=2, column=0, columnspan=2, sticky='ew', pady=4)
        (self.existing_hvac_widgets, self.existing_hvac_temperature_widgets,
         self.availability_combo) = _existing_hvac_widgets(existing, self.vars)

        plan = ttk.LabelFrame(body, text='Plan, outputs and run', padding=6)
        plan.grid(row=3, column=0, columnspan=2, sticky='ew', pady=4)
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
        self.tree.master.grid(row=4, column=0, columnspan=2, sticky='nsew', pady=4)
        ttk.Label(body, text='The model gets accim with each combination of the parameters (the coefficients of the '
                             'custom model that are not parameters take the default values), and the results are the '
                             'sums of the meters over the run period of each simulation. Other outputs, objectives, '
                             'optimisations, the m-n filter and the plots need Python: see the parametric and '
                             'optimisation section of the documentation.',
                  foreground='gray25', wraplength=900).grid(row=5, column=0, columnspan=2, sticky='w')
        self.vars['parameters_type'].trace_add('write', lambda *args: self.update_state())
        self.vars['sampling'].trace_add('write', lambda *args: self.update_state())
        self.vars['script_type'].trace_add('write', lambda *args: self.update_state())
        self.update_state()

    def update_state(self) -> None:
        """The parameters of the type of model, the number of samples only for the Latin hypercube, and the options of
        the existing HVAC systems only with them."""
        names = list(forms.PARAMETERS_TYPES.get(self.vars['parameters_type'].get(), ()))
        self.parameter_combo.configure(values=names)
        if self.parameter_name.get() not in names:
            self.parameter_name.set(names[0] if names else '')
        _set_state([self.samples_entry], self.vars['sampling'].get() == 'lhs')
        _set_existing_hvac_state(self.existing_hvac_widgets, self.existing_hvac_temperature_widgets,
                                 self.availability_combo, self.vars['script_type'].get().startswith('ex'))

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

    def clear_results(self) -> None:
        """Remove the results shown (when a session without results is opened)."""
        self.results = None
        self.tree.delete(*self.tree.get_children())
        self.tree.configure(columns=())
        self.count.set('')
        self.export_button.state(['disabled'])

    def state(self) -> Dict[str, Any]:
        return dict(super().state(), epws=_selected(self.epw_list), parameters=self.parameter_rows())

    def restore(self, state: Mapping[str, Any], results=None) -> List[str]:
        """Set the fields of the tab, and show the results of the session (``results``), if it has them."""
        messages = super().restore(state)
        messages += _file_messages(self.vars['idf'].get(), forms.input_idfs(self.folder.get()),
                                   'Input IDF of "7. Parametric study"')
        if 'epws' in state:
            messages += _select(self.epw_list, state['epws'], 'EPWs of "7. Parametric study"')
        if 'parameters' in state:
            _set_rows(self.parameter_tree, state['parameters'])
        self.update_state()
        if results is None:
            self.clear_results()
        else:
            self.show_results(results)
        return messages

    def export(self) -> None:
        if self.results is not None:
            _export_dataframe(self.app, self.results, self.folder.get(), 'accim_parametric_results.csv')


class AccimApp:
    """The main window of the graphical user interface of accim.

    :param root: The tkinter window; a new one if None.
    :ivar add_accis: The tab that adds the ACCIS.
    :ivar apmv: The tab of the PMV-based setpoints (aPMV, ePMV or PMV).
    :ivar rename_epws: The tab that renames the EPW files.
    :ivar run: The tab that runs the simulations.
    :ivar hours: The tab of the occupied hours within the setpoints.
    :ivar table: The tab of the tables and figures of the results.
    :ivar parametric: The tab of the parametric study.

    The menu *Session* saves the values of the forms and the results of the tabs in a session file
    (:meth:`save_session`) and opens it again (:meth:`open_session`).
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
        self.menu = tk.Menu(self.root, tearoff=0)
        session_menu = tk.Menu(self.menu, tearoff=0)
        session_menu.add_command(label='Open a session...', command=self.open_session)
        session_menu.add_command(label='Save the session...', command=self.save_session)
        self.menu.add_cascade(label='Session', menu=session_menu)
        self.root.configure(menu=self.menu)
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
        self.run.refresh()
        self.table.refresh()
        self.parametric.refresh()

    # Sessions
    def tabs(self) -> Dict[str, _Tab]:
        """The tabs, by the names of their attributes (the keys of their forms in the session files)."""
        return {'add_accis': self.add_accis, 'apmv': self.apmv, 'rename_epws': self.rename_epws, 'run': self.run,
                'hours': self.hours, 'table': self.table, 'parametric': self.parametric}

    def session_objects(self) -> Dict[str, Any]:
        """The objects of the session file of the window: the values of the forms
        (:data:`accim.gui.tasks.SESSION_FORMS`: the working folder and the fields of each tab) and the results of the
        tabs that have them (``table``, ``hours_within_setpoints`` and ``parametric_results``)."""
        forms_state = {'folder': self.folder.get(), **{key: tab.state() for key, tab in self.tabs().items()}}
        objects: Dict[str, Any] = {tasks.SESSION_FORMS: forms_state}
        if self.table.table is not None:
            objects['table'] = self.table.table
        if self.hours.shown is not None:
            objects['hours_within_setpoints'] = self.hours.shown
        if self.parametric.results is not None:
            objects['parametric_results'] = self.parametric.results
        return objects

    def save_session(self, path: Optional[str] = None) -> bool:
        """Save the session: the values of the forms and the results of the tabs, in a pickle file, which
        :meth:`open_session` opens, and in a JSON file with the same name, to read it (in a thread).

        :param path: The path of the pickle file; if None, a dialog asks for it.
        """
        if path is None:
            path = filedialog.asksaveasfilename(
                parent=self.root, defaultextension='.pkl', initialdir=self.folder.get(),
                initialfile='accim_session.pkl', filetypes=SESSION_FILE_TYPES,
                title='Save the session (a pickle file, and a JSON file with the same name to read it)')
            if not path:
                return False
        # The task runs in the folder of the file, so a relative path would be read from there again
        path = os.path.abspath(path)
        objects = self.session_objects()
        return self.run_task('Save the session', _folder_of(path), lambda: tasks.save_session(path, objects))

    def open_session(self, path: Optional[str] = None) -> bool:
        """Open a session saved by :meth:`save_session`, which replaces the values of the forms and the results of the
        tabs (in a thread).

        :param path: The path of the pickle file; if None, a dialog asks for it.
        """
        if path is None:
            path = filedialog.askopenfilename(parent=self.root, initialdir=self.folder.get(),
                                              filetypes=SESSION_FILE_TYPES, title='Open a session of accim')
            if not path:
                return False
        path = os.path.abspath(path)
        return self.run_task('Open a session', _folder_of(path), lambda: tasks.open_session(path),
                             on_done=self.restore_session)

    def restore_session(self, session: Mapping[str, Any]) -> None:
        """Set the working folder, the fields of the tabs and their results to those of a session (the objects of
        :func:`accim.gui.tasks.open_session`); the log shows the files of the session that are not in the folder."""
        forms_state = session[tasks.SESSION_FORMS]
        messages: List[str] = []
        folder = forms_state.get('folder', '')
        if folder and os.path.isdir(folder):
            # The tabs list the files of the folder before their selections are restored
            self.folder.set(folder)
        elif folder:
            messages.append(f'The working folder of the session, {folder}, does not exist: the tabs keep '
                            f'{self.folder.get()}.')
        results = {'table': session.get('table'), 'hours': session.get('hours_within_setpoints'),
                   'parametric': session.get('parametric_results')}
        for key, tab in self.tabs().items():
            if key in results:
                messages += tab.restore(forms_state.get(key, {}), results[key])
            else:
                messages += tab.restore(forms_state.get(key, {}))
        self.log_text('The forms and the results of the session have been restored.\n'
                      + ''.join(f'    {message}\n' for message in messages))

    # Dialogs (the tests replace them)
    def show_error(self, title: str, message: str) -> None:
        messagebox.showerror(title, message, parent=self.root)

    def show_info(self, title: str, message: str) -> None:
        messagebox.showinfo(title, message, parent=self.root)

    def ask_yes_no(self, title: str, message: str) -> bool:
        return messagebox.askyesno(title, message, parent=self.root)

    def ask_from_task(self, title: str, message: str) -> bool:
        """Ask a question with the answers yes and no from a task, in its thread: the window asks it in a dialog
        (:meth:`ask_yes_no`, in the thread of tkinter) while the task waits for the answer. In the thread of the
        window (as when the tests run a task there), the dialog opens directly."""
        if threading.current_thread() is threading.main_thread():
            return bool(self.ask_yes_no(title, message))
        answer: Dict[str, bool] = {}
        event = threading.Event()
        self.messages.put(('ask', title, message, answer, event))
        event.wait()
        return answer.get('yes', False)

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
                 answers: Optional[Mapping[str, Any]] = None) -> bool:
        """Run a task in a thread, in a folder; its output goes to the log, and ``on_done(result)`` runs when it ends.

        :param answers: The answers to the questions of the prompt that the task asks (the beginning of each question
            -> its answer, or a function of the question and of what the task has printed that returns it); the other
            questions stop the task with an error.
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
                answers: Optional[Mapping[str, Any]] = None) -> None:
        """Run a task in the current thread: in its folder, with what it prints, and its end, in the queue of
        messages, which :meth:`process_messages` shows."""
        writer = _QueueWriter(self.messages)
        cwd = os.getcwd()
        try:
            with contextlib.redirect_stdout(writer), contextlib.redirect_stderr(writer), \
                    _no_prompts(answers, writer.text):
                os.chdir(folder)
                result = function()
        except Exception as error:  # noqa: BLE001 (any error of the task is shown)
            self.messages.put(('error', title, error, traceback.format_exc()))
        else:
            self.messages.put(('done', title, result, on_done))
        finally:
            os.chdir(cwd)

    def process_messages(self) -> None:
        """Show the output of the task, the questions that it asks and its end (in the thread of tkinter)."""
        try:
            while True:
                message = self.messages.get_nowait()
                if message[0] == 'text':
                    self.log_text(message[1])
                elif message[0] == 'ask':
                    _, title, text, answer, event = message
                    try:
                        answer['yes'] = bool(self.ask_yes_no(title, text))
                    finally:
                        event.set()
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
                    text = f'{title} failed:\n\n{error}'
                    if isinstance(error, ValueError) and 'new Python session' in str(error):
                        text += ('\n\nThe window reads the IDFs with the IDD of the first EnergyPlus version that it '
                                 'has read: to work with the IDFs of another version, save the session, close the '
                                 'window, open it again and open the session.')
                    self.show_error(title, text)
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
