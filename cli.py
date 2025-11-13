import sys
import asyncio
import datetime
from typing import Any

from prompt_toolkit import Application, ANSI, PromptSession
from prompt_toolkit.application import get_app
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import Window, HSplit
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, ConditionalContainer, FloatContainer, Float
from prompt_toolkit.layout.controls import FormattedTextControl, BufferControl
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import has_focus, Condition
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.widgets import Frame, Dialog, Button, Label
from prompt_toolkit.styles import Style

from db import Dataset
from craft import CraftItem


class AppState:

    def __init__(self, db_file: str, table_name: str):
        self.db_file = db_file
        self.table_name = table_name
        self.headers: list[str] = []
        self.view_data: list[dict[str, Any]] = []
        self.all_data: list[dict[str, Any]] = []

        self.selected_row_index: int = 0
        self.selected_col_index: int = 0
        self.top_row_index: int = 0
        self.is_editing: bool = False

        self.filter_enabled: bool = False
        self.sort_enabled: bool = False
        self.filter_text: str = ""
        self.sort_text: str = ""
        self.info_text: str = ""

        self.load_data()

    def load_data(self):
        with Dataset(self.db_file, self.table_name) as db:
            self.headers = db.head_name()
            self.all_data = db.dquery_all()
        self.headers.append("eqv")
        for row in self.all_data:
            row["eqv"] = CraftItem(
                row.get("tier1_count", 0), row.get("tier2_count", 0), row.get("tier3_count", 0),
                name=row.get("item_name", ""), only_eqv=True
            )
        self.apply_filter_and_sort()

    def update(self, update_dict) -> bool:
        with Dataset(self.db_file, self.table_name) as db:
            res = db.update(update_dict)
        self.load_data()
        return res

    def apply_filter_and_sort(self):
        if self.filter_enabled:
            now = datetime.datetime.now()
            today_weekday = now.weekday()
            if now.hour < 4: today_weekday = (today_weekday + 6) % 7
            day_map = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"}
            self.info_text = f"Today is {day_map[today_weekday]} (change at 4:00 A.M)"
            if today_weekday == 6:
                key, value = None, None
            else:
                today_key_index = (today_weekday % 3) + 1
                key, value = "open_day", today_key_index
            if key:
                self.filter_text = f"Filter: {key}={value}"
                self.view_data = [row for row in self.all_data if str(row.get(key, '')) == str(value)]
            else:
                self.filter_text = "Filter: All Days"
                self.view_data = self.all_data[:]
        else:
            self.filter_text = "Filter: Off"
            self.view_data = self.all_data[:]
            self.info_text = ""

        if self.sort_enabled and "eqv" in self.headers:
            self.view_data.sort(key=lambda row: row["eqv"])
            self.sort_text = "Sort: By EQV"
        else:
            if "country" in self.headers and "open_day" in self.headers:
                self.view_data.sort(key=lambda row: (row.get("country",""), str(row.get("open_day", ""))))
            self.sort_text = "Sort: Default"
        if self.selected_row_index >= len(self.view_data):
            self.selected_row_index = max(0, len(self.view_data) - 1)


class TableApp:

    def __init__(self, state: AppState):
        self.state = state
        self.date_text = ""
        self.loggint_text = ""
        self.buffers: list[list[Buffer]] = []
        self._update_buffers()
        self.kb = KeyBindings()
        self._setup_key_bindings()
        self.app = Application(Layout(Window(height=1)))
        self.height_remain_for_other = 6
        self.table_frame = Frame(
            title=f"Table: {self.state.table_name}",
            body=HSplit(self._get_table_rows_layout(), padding=0)
        )
        self.status_bar = Window(height=1, content=FormattedTextControl(self._get_status_text), style="bg:#000080 #ffffff")
        self.help_bar = Window(height=1, content=FormattedTextControl(self._get_help_text), style="bg:#000040 #ffffff")
        self.logging_bar = Window(height=1, content=FormattedTextControl(self._get_log_text), style="bg:#000080 #ffffff")
        root_container = HSplit([
            self.table_frame,
            self.status_bar,
            self.help_bar,
            self.logging_bar,
        ])
        self.layout = Layout(root_container)
        self.app = Application(layout=self.layout, key_bindings=self.kb, full_screen=True, mouse_support=True)
        self.app.timeoutlen = 0
        self.app.ttimeoutlen = 0
        style_list = [
            ('header',         'bg:ansibrightblack fg:ansiwhite bold'),
            ('header.border',  'bg:ansibrightblack'),
            ('cell',           'bg:ansigray'),
            ('cell.border',    'bg:ansigray'),
            ('cell.selected',  'bg:ansiblue fg:ansiwhite'),
            ('cell.editing',   'bg:ansigreen fg:ansiblack'),
        ]
        self.app.style = Style(style_list)

    def _update_buffers(self):
        self.buffers = []
        for row_data in self.state.view_data:
            row_buffers = []
            for header in self.state.headers:
                buf = Buffer()
                buf.text = str(row_data[header])
                row_buffers.append(buf)
            self.buffers.append(row_buffers)

    def _get_table_rows_layout(self):
        num = len(self.state.headers)
        layouts = []
        layouts.append(VSplit([
            Window(
                FormattedTextControl(f"{h}"), style="class:header", height=1, ignore_content_width=True
            ) for h in self.state.headers
        ], padding=1, padding_style="class:header.border"))
        if not self.buffers:
            layouts.append(Window(FormattedTextControl(" --- No data available --- ")))
            return layouts
        height, width = self.app.output.get_size()
        visible_rows_count = height - self.height_remain_for_other
        self.state.top_row_index = max(0, min(self.state.top_row_index, len(self.buffers) - 1))
        visible_buffers = self.buffers[self.state.top_row_index : self.state.top_row_index + visible_rows_count]
        for i, row_buffers in enumerate(visible_buffers):
            current_row_index = self.state.top_row_index + i
            is_selected_row = (current_row_index == self.state.selected_row_index)
            cell_windows = []
            for j, buf in enumerate(row_buffers):
                is_selected_cell = is_selected_row and (j == self.state.selected_col_index)
                style = "class:cell"
                if self.state.is_editing and is_selected_cell:
                    style = "class:cell.editing"
                elif is_selected_cell:
                    style = "class:cell.selected"
                if self.state.is_editing and is_selected_cell:
                    cell_windows.append(Window(
                        content=BufferControl(buffer=buf, focusable=True),
                        style=style,
                        height=1,
                        ignore_content_width=True,
                    ))
                else:
                    cell_windows.append(Window(
                        content=FormattedTextControl(text=buf.text),
                        style=style,
                        height=1,
                        ignore_content_width=True,
                    ))
            layouts.append(VSplit(cell_windows, padding=1, padding_style="class:cell.border"))
        return layouts

    def _get_status_text(self):
        total = len(self.state.all_data)
        showing = len(self.state.view_data)
        left_text = (
            f" {self.state.filter_text} | {self.state.sort_text} | "
            f"Rows: {showing}/{total} | At ({self.state.selected_row_index}, {self.state.selected_col_index})"
        )
        right_text = f" {self.date_text} {self.state.info_text} "

        if self.status_bar and self.status_bar.render_info:
            width = self.status_bar.render_info.window_width
            padding = width - len(left_text) - len(right_text)
            if padding > 0:
                return left_text + (" " * padding) + right_text
        return left_text

    def _get_help_text(self):
        if self.state.is_editing:
            return " [Enter] Save & Exit | [Esc] Cancel Edit "
        else:
            return " [j/k/h/l] Navigate | [Enter/e] Edit | [f] Toggle Filter | [s] Toggle Sort | [r] Reload | [q] Quit "

    def _get_log_text(self):
        return self.loggint_text

    def _update_layout(self):
        self.table_frame.body = HSplit(self._get_table_rows_layout(), padding=0)
        self.app.invalidate()

    def _adjust_scroll(self):
        height, width = self.app.output.get_size()
        visible_rows_count = height - self.height_remain_for_other
        if self.state.selected_row_index < self.state.top_row_index:
            self.state.top_row_index = self.state.selected_row_index
        elif self.state.selected_row_index >= self.state.top_row_index + visible_rows_count:
            self.state.top_row_index = self.state.selected_row_index - visible_rows_count + 1
        self._update_layout()

    def _setup_key_bindings(self):

        kb_nav = KeyBindings()

        @kb_nav.add("q")
        def _(event): event.app.exit()

        @kb_nav.add("j")
        @kb_nav.add("down")
        def _(event): self._move_cursor(1, 0)

        @kb_nav.add("k")
        @kb_nav.add("up")
        def _(event): self._move_cursor(-1, 0)

        @kb_nav.add("l")
        @kb_nav.add("right")
        def _(event): self._move_cursor(0, 1)

        @kb_nav.add("h")
        @kb_nav.add("left")
        def _(event): self._move_cursor(0, -1)

        @kb_nav.add("e")
        @kb_nav.add("enter")
        def _(event): self._start_editing()

        @kb_nav.add("f")
        def _(event):
            self.state.filter_enabled = not self.state.filter_enabled
            self.state.apply_filter_and_sort()
            self._update_buffers()
            self._update_layout()

        @kb_nav.add("s")
        def _(event):
            self.state.sort_enabled = not self.state.sort_enabled
            self.state.apply_filter_and_sort()
            self._update_buffers()
            self._update_layout()

        @kb_nav.add("r")
        def _(event):
            self.state.load_data()
            self._update_buffers()
            self._update_layout()

        kb_edit = KeyBindings()

        @kb_edit.add("escape")
        def _(event): self._cancel_editing()

        @kb_edit.add("enter")
        def _(event): self._save_and_stop_editing()

        is_editing_filter = Condition(lambda: self.state.is_editing)
        self.kb.bindings.extend(kb_nav.bindings)
        self.kb.bindings.extend(kb_edit.bindings)
        for binding in self.kb.bindings:
            if binding in kb_nav.bindings:
                binding.filter = ~is_editing_filter
            elif binding in kb_edit.bindings:
                binding.filter = is_editing_filter

    def _move_cursor(self, dr, dc):
        new_row = self.state.selected_row_index + dr
        new_col = self.state.selected_col_index + dc
        if 0 <= new_row < len(self.buffers):
            self.state.selected_row_index = new_row
        if 0 <= new_col < len(self.state.headers):
            self.state.selected_col_index = new_col
        self._adjust_scroll()

    def _start_editing(self):
        header = self.state.headers[self.state.selected_col_index]
        if header.lower() in ['eqv']:
            self.loggint_text = f"'{header}' column is read-only."
            self.app.invalidate()
            return
        self.state.is_editing = True
        target_buffer = self.buffers[self.state.selected_row_index][self.state.selected_col_index]
        self._update_layout()
        for w in self.app.layout.find_all_windows():
            if isinstance(w.content, BufferControl) and w.content.buffer == target_buffer:
                self.app.layout.focus(w)
                break

    def _cancel_editing(self):
        original_text = str(self.state.view_data[self.state.selected_row_index].get(self.state.headers[self.state.selected_col_index], ""))
        self.buffers[self.state.selected_row_index][self.state.selected_col_index].text = original_text
        self.state.is_editing = False
        self.loggint_text = f"remain {original_text}"
        self._update_layout()

    def _save_and_stop_editing(self):
        self.state.is_editing = False
        update_dict = {}
        for i, key in enumerate(self.state.headers):
            if key in ['eqv']: continue
            update_dict[key] = self.buffers[self.state.selected_row_index][i].text
        res = self.state.update(update_dict)
        self.loggint_text = f"update {res}: {update_dict}"
        self._update_layout()

    async def _background_updater(self):
        while True:
            self.date_text = datetime.datetime.now().strftime("%H:%M:%S")
            self.app.invalidate()
            await asyncio.sleep(1)

    async def run(self):
        update_task = asyncio.create_task(self._background_updater())
        await self.app.run_async()
        update_task.cancel()


if __name__ == "__main__":
    db_file = "game.db"
    if len(sys.argv) != 2:
        table_name = "genshin_materials"
    else:
        table_name = sys.argv[1]
    app_state = AppState(db_file, table_name)
    app_ui = TableApp(app_state)
    asyncio.run(app_ui.run())
