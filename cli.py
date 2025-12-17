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

from db import Dataset, Scheme
from craft import CraftItem
import scheme.genshin, scheme.starrail


class AppState:
    # CONSTRAIN = "id"
    # GENERATE_LIST = ["eqv"]

    def __init__(
        self, db_file: str, table_name: str,
        *,
        create_scheme: Scheme | None = None,
        create_data: list[dict] | None = None
    ):
        self.db_file = db_file
        self.table_name = table_name
        self.create_scheme = create_scheme
        self.create_data = create_data

        self.headers: list[str] = []
        self.view_data: list[dict[str, Any]] = []
        self.all_data: list[dict[str, Any]] = []

        self.selected_row_index: int = 0
        self.selected_col_index: int = 1  # strip "id"
        self.top_row_index: int = 0
        self.is_editing: bool = False
        self.show_id: bool = False

        self.has_filter: bool = self.table_name.startswith("genshin")
        self.filter_enabled: bool = False
        self.sort_enabled: int = 0
        self.filter_text: str = ""
        self.sort_text: str = ""
        self.info_text: str = ""

        self.load_data()

    def load_data(self):
        with Dataset(
            self.db_file, self.table_name,
            create_scheme=self.create_scheme, create_data=self.create_data
        ) as db:
            self.headers = db.head_name()
            self.all_data = db.dquery_all()
        self.headers.append("eqv")
        for row in self.all_data:
            row["eqv"] = CraftItem(
                *(list(row.values())[3:]),
                name=row.get("item_name", ""), only_eqv=True
            )
        self.apply_filter_and_sort()

    def update(self, line_id, new_dict: dict) -> bool:
        try:
            old_id = int(line_id)
        except Exception:
            self.info_text = f"Update error: invalid id={line_id!r}"
            return False

        new_dict = dict(new_dict)
        new_dict.pop("eqv", None)

        if "id" in new_dict:
            try:
                new_id = int(new_dict["id"])
            except Exception:
                self.info_text = f"Update error: new id must be int, got {new_dict['id']!r}"
                return False

            if new_id != old_id:
                with Dataset(self.db_file, self.table_name) as db:
                    exists = db.dquery_constrain({"id": new_id})
                if exists:
                    self.info_text = f"Update error: id={new_id} already exists"
                    return False

            new_dict["id"] = new_id

        with Dataset(self.db_file, self.table_name) as db:
            rows = db.dquery_constrain({"id": old_id})
            if not rows:
                self.info_text = f"Update error: row id={old_id} not found"
                return False

            res = db.update_where({"id": old_id}, new_dict)

        self.load_data()
        return res

    def delete(self, old_dict) -> bool:
        line_id = old_dict["id"] if isinstance(old_dict, dict) else old_dict
        with Dataset(self.db_file, self.table_name) as db:
            res = db.delete({"id": int(line_id)})
        self.load_data()
        return res

    def insert(self, new_dict) -> bool:
        new_dict = dict(new_dict)
        new_dict.pop("eqv", None)
        with Dataset(self.db_file, self.table_name) as db:
            res = db.insert_or_update(new_dict)
        self.load_data()
        return res

    def apply_filter_and_sort(self):
        if self.has_filter and self.filter_enabled:
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

        if self.sort_enabled == 1:
            self.view_data.sort(key=lambda row: row["eqv"])
            self.sort_text = "Sort: Eqv"
        elif self.sort_enabled == 2:
            self.view_data.sort(key=lambda row: (row[self.headers[1]], str(row[self.headers[2]])))  # strip "id"
            self.sort_text = "Sort: Name"
        else:
            self.view_data.sort(key=lambda row: row["id"])
            self.sort_text = "Sort: Default"
        if self.selected_row_index >= len(self.view_data):
            self.selected_row_index = max(0, len(self.view_data) - 1)

    def _id_set(self) -> set[int]:
        s = set()
        for r in self.all_data:
            try:
                s.add(int(r["id"]))
            except Exception:
                pass
        return s

    def id_exists(self, new_id: int) -> bool:
        return int(new_id) in self._id_set()

    def next_bottom_id(self) -> int:
        ids = sorted(self._id_set())
        return (ids[-1] + 1) if ids else 1

    def compute_insert_id(self, current_id: int) -> int:
        current_id = int(current_id)
        if self.sort_enabled == 0 and (current_id + 1) not in self._id_set():
            return current_id + 1
        return self.next_bottom_id()

    def blank_row_dict(self, new_id: int) -> dict[str, Any]:
        d: dict[str, Any] = {}
        for h in self.headers:
            if h == "eqv":
                continue
            if h == "id":
                d["id"] = int(new_id)
            else:
                d[h] = ""
        return d

    def find_view_row_index_by_id(self, row_id: int) -> int | None:
        for i, r in enumerate(self.view_data):
            try:
                if int(r["id"]) == int(row_id):
                    return i
            except Exception:
                continue
        return None


class TableApp:

    def __init__(self, state: AppState):
        self.state = state
        self.date_text = ""
        self.logging_text = ""
        self.buffers: list[list[Buffer]] = []
        self._update_buffers()
        self.kb = KeyBindings()
        self._setup_key_bindings()
        self.app = Application(Layout(Window(height=1)))
        self.height_remain_for_other = 6
        self.table_frame = Frame(
            title=f"Table: {self.state.table_name}",
            body=HSplit(self._get_table_rows_layout(), padding=0),
        )
        self.status_bar = Window(height=1, content=FormattedTextControl(self._get_status_text))
        self.help_bar = Window(height=1, content=FormattedTextControl(self._get_help_text))
        self.logging_bar = Window(height=1, content=FormattedTextControl(self._get_log_text))
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
            ('header',         'bg:ansibrightblack fg:#ffffff bold'),
            ('header.border',  'bg:ansibrightblack'),
            ('cell',           'bg:ansigray fg:#222222'),
            ('cell.border',    'bg:ansigray'),
            ('cell.selected',  'bg:ansiblue fg:#ffffff'),
            ('cell.editing',   'bg:ansigreen fg:#ffffff'),
        ]
        self.app.style = Style(style_list)
        self._pending_delete: bool = False

    def _update_buffers(self):
        self.buffers = []
        for row_data in self.state.view_data:
            row_buffers = []
            for header in self.state.headers:
                buf = Buffer()
                buf.text = str(row_data[header])
                row_buffers.append(buf)
            self.buffers.append(row_buffers)

    def _focus_row_by_id(self, row_id: int) -> bool:
        idx = self.state.find_view_row_index_by_id(row_id)
        if idx is None:
            return False
        self.state.selected_row_index = idx
        return True

    def _visible_headers(self) -> list[str]:
        # 是否显示 id 由 state.show_id 控制；eqv 永远显示（但不可编辑）
        if self.state.show_id:
            return self.state.headers[:]  # 包含 id, ... , eqv
        else:
            return [h for h in self.state.headers if h != "id"]

    def _col_to_real_index(self, visible_col_index: int) -> int:
        vh = self._visible_headers()
        header = vh[visible_col_index]
        return self.state.headers.index(header)

    def _real_to_visible_index(self, real_index: int) -> int:
        rh = self.state.headers[real_index]
        vh = self._visible_headers()
        return vh.index(rh)

    def _get_table_rows_layout(self):
        num = len(self.state.headers)
        layouts = []
        visible_headers = self._visible_headers()
        layouts.append(VSplit([
            Window(
                FormattedTextControl(f"{h}"), style="class:header", height=1, ignore_content_width=True
            ) for h in visible_headers
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
            for visible_j, header in enumerate(visible_headers):
                real_j = self.state.headers.index(header)
                buf = row_buffers[real_j]
                is_selected_cell = is_selected_row and (real_j == self.state.selected_col_index)
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
        filter_data = f" {self.state.filter_text} |" if self.state.has_filter else ""
        # 显示可见列坐标
        visible_headers = self._visible_headers()
        current_header = self.state.headers[self.state.selected_col_index]
        try:
            visible_col = visible_headers.index(current_header)
        except ValueError:
            visible_col = 0
        left_text = (
            f"{filter_data} {self.state.sort_text} | "
            f"Rows: {showing}/{total} | At ({self.state.selected_row_index}, {visible_col})"
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
            filter_data = " | [f] Toggle Filter" if self.state.has_filter else ""
            id_data = " | [i] Toggle ID"  # Feature 1
            return f" [j/k/h/l] Navigate | [Enter/e] Edit{filter_data} | [s] Toggle Sort | [a/o] Add | [d] Delete{id_data} | [r] Reload | [q] Quit "

    def _get_log_text(self):
        return self.logging_text

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
            if self.state.has_filter:
                self.state.filter_enabled = not self.state.filter_enabled
                self.state.apply_filter_and_sort()
                self._update_buffers()
                self._update_layout()

        @kb_nav.add("s")
        def _(event):
            self.state.sort_enabled = (self.state.sort_enabled + 1) % 3
            self.state.apply_filter_and_sort()
            self._update_buffers()
            self._update_layout()

        @kb_nav.add("r")
        def _(event):
            self.state.load_data()
            self._update_buffers()
            self._update_layout()

        @kb_nav.add("a")
        @kb_nav.add("o")
        def _(event):
            self._pending_delete = False
            self._add_row()

        @kb_nav.add("i")
        def _(event):
            self.state.show_id = not self.state.show_id
            # 如果隐藏 id 且当前选中列是 id，把列移到下一个
            if not self.state.show_id and self.state.headers[self.state.selected_col_index] == "id":
                self.state.selected_col_index = 1 if len(self.state.headers) > 1 else 0

            self._update_layout()

        @kb_nav.add("d")
        def _(event):
            if self._pending_delete:
                self._confirm_delete()
            else:
                self._request_delete()

        @kb_nav.add("escape")
        def _(event): self._cancel_pending_delete()

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
        if 0 <= new_row < len(self.buffers):
            self.state.selected_row_index = new_row

        if dc != 0:
            visible_headers = self._visible_headers()
            current_header = self.state.headers[self.state.selected_col_index]
            # 如果当前列不可见（例如切换隐藏 id 后），把它挪到第一个可见列
            if current_header not in visible_headers:
                self.state.selected_col_index = self.state.headers.index(visible_headers[0])
            else:
                v_idx = visible_headers.index(current_header)
                v_idx = max(0, min(len(visible_headers) - 1, v_idx + dc))
                self.state.selected_col_index = self.state.headers.index(visible_headers[v_idx])

        self._adjust_scroll()

    def _add_row(self):
        if not self.state.view_data:
            new_id = 1
        else:
            current_id = int(self.state.view_data[self.state.selected_row_index]["id"])
            new_id = self.state.compute_insert_id(current_id)

        if self.state.id_exists(new_id):
            self.logging_text = f"Add: computed id={new_id} already exists (unexpected)."
            self.app.invalidate()
            return

        new_row = self.state.blank_row_dict(new_id)
        res = self.state.insert(new_row)
        self.logging_text = f"Add {res}: id={new_id}"

        self._update_buffers()

        for idx, r in enumerate(self.state.view_data):
            if int(r["id"]) == int(new_id):
                self.state.selected_row_index = idx
                break

        if not self.state.show_id and self.state.headers[self.state.selected_col_index] == "id":
            self.state.selected_col_index = 1 if len(self.state.headers) > 1 else 0

        self._adjust_scroll()

    def _start_editing(self):
        header = self.state.headers[self.state.selected_col_index]
        if header.lower() in ['eqv']:
            self.logging_text = f"Edit: '{header}' column is read-only."
            self.app.invalidate()
            return
        if header.lower() == "id" and not self.state.show_id:
            self.logging_text = "Edit: id is hidden (press 'i' to show)."
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
        original_text = str(self.state.view_data[self.state.selected_row_index][self.state.headers[self.state.selected_col_index]])
        self.buffers[self.state.selected_row_index][self.state.selected_col_index].text = original_text
        self.state.is_editing = False
        self.logging_text = f"Remain: {original_text}"
        self._update_buffers()
        self._update_layout()

    def _save_and_stop_editing(self):
        self.state.is_editing = False

        row_index = self.state.selected_row_index
        key = self.state.headers[self.state.selected_col_index]

        # 关键：稳定旧 id 一定要从 view_data 拿
        stable_old_id = int(self.state.view_data[row_index]["id"])

        new_text = self.buffers[row_index][self.state.selected_col_index].text
        old_value = str(self.state.view_data[row_index].get(key, ""))

        if str(old_value) == str(new_text):
            self.logging_text = "Update: Not Change"
            self._update_layout()
            return

        track_id = stable_old_id
        if key == "id":
            try:
                track_id = int(new_text)
            except ValueError:
                self.logging_text = "Update: id must be an integer."
                self._update_buffers()
                self._update_layout()
                return

        res = self.state.update(stable_old_id, {key: new_text})
        if not res:
            self.logging_text = self.state.info_text or "Update: Failed"
            self._update_buffers()
            self._update_layout()
            return

        self._update_buffers()

        found = self._focus_row_by_id(track_id)
        if not found:
            self.state.selected_row_index = min(self.state.selected_row_index, max(0, len(self.state.view_data) - 1))
            self.logging_text = f"Update {res}: {key} {old_value} > {new_text} (row not visible due to filter?)"
        else:
            self.logging_text = f"Update {res}: {key} {old_value} > {new_text}"

        self._adjust_scroll()

    def _request_delete(self):
        if not self.state.view_data:
            return
        row = self.state.view_data[self.state.selected_row_index]
        self._pending_delete = True
        self.logging_text = f"Delete? id={row['id']} (press 'd' again to confirm, Esc to cancel)"
        self.app.invalidate()

    def _confirm_delete(self):
        if not self._pending_delete:
            return
        self._pending_delete = False
        row = self.state.view_data[self.state.selected_row_index]
        res = self.state.delete(row)
        self.logging_text = f"Delete {res}: id={row['id']}"
        self._update_buffers()
        self.state.selected_row_index = min(self.state.selected_row_index, max(0, len(self.state.view_data) - 1))
        self._adjust_scroll()

    def _cancel_pending_delete(self):
        if self._pending_delete:
            self._pending_delete = False
            self.logging_text = "Delete: canceled"
            self.app.invalidate()

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

    create_scheme = None
    create_data = None
    if table_name.startswith("genshin_materials"):
        create_scheme = scheme.genshin.genshin_scheme
        create_data = scheme.genshin.genshin_init_data
    elif table_name.startswith("genshin_weapon"):
        create_scheme = scheme.genshin.genshin_weapon_scheme
        create_data = scheme.genshin.genshin_weapon_init_data
    elif table_name.startswith("starrail_materials"):
        create_scheme = scheme.starrail.starrail_scheme
        create_data = scheme.starrail.starrail_init_data

    app_state = AppState(
        db_file, table_name,
        create_scheme=create_scheme,
        create_data=create_data
    )
    app_ui = TableApp(app_state)
    asyncio.run(app_ui.run())
