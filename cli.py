import sys
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.style import Style

from prompt_toolkit import Application, ANSI
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import Window, HSplit
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.shortcuts import input_dialog, yes_no_dialog
from prompt_toolkit.completion import WordCompleter

from db import Dataset
from craft import CraftItem


class AppState:
    def __init__(self, db_file: str, table_name: str):
        self.db_file = db_file
        self.table_name = table_name
        self.all_data: list[dict[str, Any]] = []
        self.view_data: list[dict[str, Any]] = []
        self.headers: list[str] = []
        self.selected_row_index: int = 0
        self.top_row_index: int = 0
        self.filter_text: str = ""
        self.sort_text: str = ""
        self.load_data()

    def load_data(self):
        with Dataset(self.db_file, self.table_name) as db:
            self.headers = db.head_name()
            self.all_data = db.dquery_all()
        self.headers.append("eqv")
        for row in self.all_data:
            row["eqv"] = CraftItem(
                row["tier1_count"], row["tier2_count"], row["tier3_count"],
                name=row["item_name"], only_eqv=True
            )
        self.apply_filter_and_sort()

    def apply_filter_and_sort(self, filter_str: str | None = None, sort: bool = False):
        if filter_str:
            self.filter_text = f"Filter: {filter_str}"
            try:
                key, value = filter_str.split('=', 1)
                key, value = key.strip(), value.strip()
                self.view_data = [row for row in self.all_data if str(row.get(key)) == value]
            except ValueError:
                self.filter_text = "Invalid Filter (use: key=value)"
                self.view_data = self.all_data
        else:
            self.filter_text = ""
            self.view_data = self.all_data

        if sort:
            self.view_data.sort(key=lambda row: row["eqv"])
        else:
            self.view_data.sort(key=lambda row: row["country"] + row["open_day"] * "A")
        self.selected_row_index = 0
        self.top_row_index = 0

class TableApp:

    sort = True

    def __init__(self, state: AppState):
        self.state = state
        self.console = Console()
        self.kb = KeyBindings()
        self._setup_key_bindings()

        self.table_window = Window(content=FormattedTextControl(text=self._get_table_text), style="bg:#ffffff #000000")
        self.status_bar = Window(height=1, content=FormattedTextControl(text=self._get_status_text), style="bg:#000080 #ffffff")
        self.help_bar = Window(height=1, content=FormattedTextControl(text=self._get_help_text), style="bg:#404040 #ffffff")

        root_container = HSplit([
            self.table_window,
            self.status_bar,
            self.help_bar,
        ])

        self.layout = Layout(root_container)
        self.app = Application(layout=self.layout, key_bindings=self.kb, full_screen=True)

    def _setup_key_bindings(self):
        @self.kb.add("q")
        def _(event):
            event.app.exit()

        @self.kb.add("down")
        @self.kb.add("j")
        def _(event):
            if self.state.selected_row_index < len(self.state.view_data) - 1:
                self.state.selected_row_index += 1
            self._adjust_scroll()

        @self.kb.add("up")
        @self.kb.add("k")
        def _(event):
            if self.state.selected_row_index > 0:
                self.state.selected_row_index -= 1
            self._adjust_scroll()

        @self.kb.add("a")
        async def _(event): await self.run_add()

        @self.kb.add("e")
        @self.kb.add("enter")
        async def _(event): await self.run_edit()

        @self.kb.add("d")
        async def _(event): await self.run_delete()

        @self.kb.add("r")
        def _(event): self.state.load_data()

        @self.kb.add("f")
        async def _(event): await self.run_filter()

        @self.kb.add("c")
        def _(event): self.state.apply_filter_and_sort()

        @self.kb.add("s")
        async def _(event): await self.run_sort()

    def _adjust_scroll(self):
        if not self.table_window.render_info:
            return
        visible_data_rows = self.table_window.render_info.window_height - 1
        if visible_data_rows <= 0:
            return
        if not self.state.view_data:
            self.state.top_row_index = 0
            self.state.selected_row_index = 0
            return
        if self.state.selected_row_index >= len(self.state.view_data):
            self.state.selected_row_index = len(self.state.view_data) - 1
        if self.state.selected_row_index >= self.state.top_row_index + visible_data_rows:
            self.state.top_row_index = self.state.selected_row_index - visible_data_rows + 1
        elif self.state.selected_row_index < self.state.top_row_index:
            self.state.top_row_index = self.state.selected_row_index

    def _get_table_text(self):
        table = Table(box=None, expand=True)
        header_style = Style(bold=True, color="cyan")
        selected_style = Style(bgcolor="dark_orange")

        for header in self.state.headers:
            table.add_column(header, style="green", header_style=header_style)

        if not self.state.view_data:
            table.add_row("No data available")
        else:
            if self.table_window.render_info:
                visible_data_rows = self.table_window.render_info.window_height - 1
                if visible_data_rows < 0:
                    visible_data_rows = 0
            else:
                visible_data_rows = 20

            visible_rows_data = self.state.view_data[self.state.top_row_index : self.state.top_row_index + visible_data_rows]

            for i, row_data in enumerate(visible_rows_data, start=self.state.top_row_index):
                row_items = [str(row_data.get(h, "")) for h in self.state.headers]
                style = selected_style if i == self.state.selected_row_index else ""
                table.add_row(*row_items, style=style)

        with self.console.capture() as capture:
            self.console.print(table)
        return ANSI(capture.get())

    def _get_status_text(self):
        total = len(self.state.all_data)
        showing = len(self.state.view_data)
        return f" Table: {self.state.db_file} | Rows: {showing}/{total} | {self.state.filter_text} | {self.state.sort_text}"

    def _get_help_text(self):
        return " [A]dd | [E]dit | [D]elete | [F]ilter | [C]lear Filter | [S]ort | [R]efresh | [Q]uit "

    async def _prompt_for_data(self, existing_data: dict | None = None) -> dict | None:
        new_data = {}
        for header in self.state.headers:
            if header.lower() == 'id':
                continue
            default_val = str(existing_data.get(header, "")) if existing_data else ""
            val = await input_dialog(
                title=f"Enter value for {header}",
                text=f"{header}:",
                default=default_val
            ).run_async()
            if val is None:
                return None
            new_data[header] = val
        return new_data

    async def run_add(self):
        new_data = await self._prompt_for_data()
        if new_data:
            with Dataset(self.state.db_file, self.state.table_name) as db:
                db.store(new_data)
            self.state.load_data()
            self.app.invalidate()

    async def run_edit(self):
        if not self.state.view_data:
            return
        selected_row = self.state.view_data[self.state.selected_row_index]
        updated_data = await self._prompt_for_data(existing_data=selected_row)
        if updated_data:
            with Dataset(self.state.db_file, self.state.table_name) as db:
                db.update(updated_data)
            self.state.load_data()
            self.app.invalidate()

    async def run_delete(self):
        if not self.state.view_data:
            return
        confirm = await yes_no_dialog(
            title="Confirm Deletion",
            text="Are you sure you want to delete this row?"
        ).run_async()

        if confirm:
            selected_row = self.state.view_data[self.state.selected_row_index]
            with Dataset(self.state.db_file, self.state.table_name) as db:
                db.delete(selected_row)
            self.state.load_data()
            self.app.invalidate()

    async def run_filter(self):
        filter_str = await input_dialog(
            title="Filter Data",
            text="Enter filter (e.g., category=Fruit):"
        ).run_async()

        if filter_str:
            self.state.apply_filter_and_sort(filter_str=filter_str)
            self.app.invalidate()

    async def run_sort(self):
        self.state.apply_filter_and_sort(sort=self.sort)
        self.sort = not self.sort
        self.app.invalidate()

    def run(self):
        self.app.run()

if __name__ == "__main__":
    db_file = "game.db"
    if len(sys.argv) != 2:
        table_name = "genshin_materials"
    else:
        table_name = sys.argv[1]
    app_state = AppState(db_file, table_name)
    app_ui = TableApp(app_state)
    app_ui.run()
