import sys
import asyncio
import datetime
from bisect import bisect_left
from typing import Callable, Any
from dataclasses import dataclass, field

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


@dataclass
class TableConfig:
    # 主键
    prikey_field: str = "id"
    prikey_type: Callable[[Any], Any] = int
    allow_edit_prikey: bool = True

    # 运行时生成的键
    generated_fields: list[str] = field(default_factory=lambda: ["eqv"])
    generators: dict[str, Callable[[dict[str, Any]], Any]] = field(default_factory=dict)

    # 默认排序和其他排序键
    default_sort_key: Callable[[dict[str, Any]], Any] | None = None
    sort_keys: dict[int, Callable[[dict[str, Any]], Any]] = field(default_factory=dict)
    sort_texts: dict[int, str] = field(default_factory=dict)

    make_blank: Callable[[list[str], Any], dict[str, Any]] | None = None


def make_eqv(row: dict[str, Any]) -> CraftItem:
    return CraftItem(
        # TODO: 目前是硬编码 3 开始是物品直到结尾，暂不更改
        *(list(row.values())[3:]),
        name=row.get("item_name", ""), only_eqv=True
    )

eqv_config = TableConfig(
    prikey_field="id",
    prikey_type=int,
    allow_edit_prikey=True,
    generated_fields=["eqv"],
    generators={"eqv": make_eqv},
    default_sort_key=lambda r: int(r["id"]),
    sort_keys={
        1: lambda r: r["eqv"],
    },
    sort_texts={
        0: "Sort: Default",
        1: "Sort: Eqv",
    }
)


class AppState:

    def __init__(
        self, db_file: str, table_name: str,
        *,
        config: TableConfig = eqv_config,
        create_scheme: Scheme | None = None,
        create_data: list[dict] | None = None
    ):
        self.db_file = db_file
        self.table_name = table_name
        self.config = config
        self.create_scheme = create_scheme
        self.create_data = create_data

        self.headers: list[str] = []
        self.view_data: list[dict[str, Any]] = []
        self.all_data: list[dict[str, Any]] = []

        self.selected_row_index: int = 0
        self.selected_col_index: int = 0
        self.top_row_index: int = 0
        self.is_editing: bool = False
        self.show_id: bool = False

        self.filter_field_name: str = "open_day"
        self.has_filter: bool
        self.filter_enabled: bool = False
        self.sort_enabled: int = 0
        self.filter_text: str = ""
        self.sort_text: str = ""
        self.info_text: str = ""

        self.header_to_index: dict[str, int] = {}
        self._cached_key_set: set[Any] = set()

        self.load_data()

    def load_data(self):
        with Dataset(
            self.db_file, self.table_name,
            create_scheme=self.create_scheme, create_data=self.create_data
        ) as db:
            db_headers = db.head_name()
            self.all_data = db.dquery_all()

        self.headers = db_headers[:]
        self.has_filter = (self.filter_field_name in self.headers)

        for g in self.config.generated_fields:
            if g not in self.headers:
                self.headers.append(g)

        for row in self.all_data:
            for g in self.config.generated_fields:
                gen = self.config.generators.get(g)
                row[g] = "" if gen is None else gen(row)

        self.apply_filter_and_sort()
        self._rebuild_caches()
        self._normalize_selected_col()

    def update(self, old_prikey_value: Any, new_dict: dict) -> bool:
        prikey_field = self.config.prikey_field
        new_dict = self._strip_generated(new_dict)

        try:
            old_prikey_value = self.config.prikey_type(old_prikey_value)
        except Exception:
            self.info_text = f"Update error: invalid {prikey_field}={old_prikey_value!r}"
            return False

        if prikey_field in new_dict:
            try:
                new_prikey_value = self.config.prikey_type(new_dict[prikey_field])
            except Exception:
                self.info_text = f"Update error: {prikey_field} must be int, got {new_dict[prikey_field]!r}"
                return False

            if new_prikey_value != old_prikey_value:
                with Dataset(self.db_file, self.table_name) as db:
                    exists = db.dquery_constrain({prikey_field: new_prikey_value})
                if exists:
                    self.info_text = f"Update error: {prikey_field}={new_prikey_value} already exists"
                    return False

            new_dict[prikey_field] = new_prikey_value

        with Dataset(self.db_file, self.table_name) as db:
            rows = db.dquery_constrain({prikey_field: old_prikey_value})
            if not rows:
                self.info_text = f"Update error: row {prikey_field}={old_prikey_value} not found"
                return False
            res = db.update_where({prikey_field: old_prikey_value}, new_dict)

        self.load_data()
        return res

    def delete(self, old_row_or_prikey_value: dict | Any) -> bool:
        prikey_field = self.config.prikey_field
        prikey_value = old_row_or_prikey_value[prikey_field] if isinstance(old_row_or_prikey_value, dict) else old_row_or_prikey_value
        with Dataset(self.db_file, self.table_name) as db:
            res = db.delete({prikey_field: self.config.prikey_type(prikey_value)})
        self.load_data()
        return res

    def insert(self, new_dict) -> bool:
        new_dict = dict(new_dict)
        new_dict = self._strip_generated(new_dict)
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
                key, value = self.filter_field_name, today_key_index
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

        prikey_field = self.config.prikey_field

        if self.sort_enabled == 0:
            if self.config.default_sort_key:
                self.view_data.sort(key=self.config.default_sort_key)
            else:
                self.view_data.sort(key=lambda r: self.config.prikey_type(r[prikey_field]))
            self.sort_text = self.config.sort_texts.get(0, "Sort: Default")
        else:
            sk = self.config.sort_keys.get(self.sort_enabled)
            if sk:
                self.view_data.sort(key=sk)
                self.sort_text = self.config.sort_texts.get(self.sort_enabled, f"Sort: {self.sort_enabled}")
            else:
                # fallback
                self.view_data.sort(key=lambda r: self.config.prikey_type(r[prikey_field]))
                self.sort_text = "Sort: Default"

    def prikey_exists(self, prikey_value: Any) -> bool:
        try:
            return self.config.prikey_type(prikey_value) in self._cached_key_set
        except Exception:
            return False

    def insert_key_position(self, current_key: Any) -> Any:
        current_key = self.config.prikey_type(current_key)
        if self.sort_enabled == 0 and (current_key + 1) not in self._key_set():
            return current_key + 1
        return self._next_bottom_key()

    def blank_row_dict(self, new_key: Any) -> dict[str, Any]:
        headers_without_generated = [h for h in self.headers if h not in self.config.generated_fields]
        if self.config.make_blank:
            return self.config.make_blank(headers_without_generated, new_key)
        d: dict[str, Any] = {}
        for h in headers_without_generated:
            if h == self.config.prikey_field:
                d[h] = self.config.prikey_type(new_key)
            else:
                d[h] = ""
        return d

    def _rebuild_caches(self):
        self.header_to_index = {h: i for i, h in enumerate(self.headers)}
        pk = self.config.prikey_field
        cast = self.config.prikey_type
        s: set[Any] = set()
        for r in self.all_data:
            try:
                s.add(cast(r[pk]))
            except Exception:
                pass
        self._cached_key_set = s

    def _key_set(self) -> set[Any]:
        return self._cached_key_set

    def _next_bottom_key(self) -> Any:
        # TODO: 假设 key 可比较且可 +1，暂不更改
        keys = sorted(self._cached_key_set)
        return (keys[-1] + 1) if keys else 1

    def _find_view_row_index_by_prikey(self, prikey_value: Any) -> int | None:
        prikey_field = self.config.prikey_field
        for i, r in enumerate(self.view_data):
            try:
                if self.config.prikey_type(r[prikey_field]) == self.config.prikey_type(prikey_value):
                    return i
            except Exception:
                continue
        return None

    def _strip_generated(self, d: dict[str, Any]) -> dict[str, Any]:
        d = dict(d)
        for g in self.config.generated_fields:
            d.pop(g, None)
        return d

    def _normalize_selected_col(self):
        if not self.headers:
            self.selected_col_index = 0
            return
        self.selected_col_index = max(0, min(self.selected_col_index, len(self.headers) - 1))
        pk = self.config.prikey_field
        generated = set(self.config.generated_fields)
        def is_visible(h: str) -> bool:
            return self.show_id or h != pk
        def is_editable(h: str) -> bool:
            if h in generated:
                return False
            if h == pk and not self.config.allow_edit_prikey:
                return False
            if not is_visible(h):
                return False
            return True
        current_h = self.headers[self.selected_col_index]
        if is_editable(current_h):
            return
        for i, h in enumerate(self.headers):
            if is_editable(h):
                self.selected_col_index = i
                return
        for i, h in enumerate(self.headers):
            if is_visible(h) and h not in generated:
                self.selected_col_index = i
                return
        self.selected_col_index = 0


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

    def _visible_headers(self) -> list[str]:
        prikey_field = self.state.config.prikey_field
        if self.state.show_id:
            return self.state.headers[:]
        return [h for h in self.state.headers if h != prikey_field]

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
            filter_data = " | [f] Filter" if self.state.has_filter else ""
            return f" [j/k/h/l] Navigate | [Enter/e] Edit{filter_data} | [s] Sort | [a/o] Add | [d] Delete | [i] ID | [r] Reload | [q] Quit "

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

    def _focus_row_by_prikey(self, prikey_value: Any) -> bool:
        idx = self.state._find_view_row_index_by_prikey(prikey_value)
        if idx is None:
            return False
        self.state.selected_row_index = idx
        return True

    def _get_selected_prikey(self) -> int | None:
        if not self.state.view_data:
            return None
        prikey_field = self.state.config.prikey_field
        cast = self.state.config.prikey_type
        r = self.state.view_data[self.state.selected_row_index]
        try:
            return cast(r[prikey_field])
        except Exception:
            return None

    def _restore_focus_by_prikey_or_next(self, pk_value: int | None):
        if not self.state.view_data:
            self.state.selected_row_index = 0
            return
        prikey_field = self.state.config.prikey_field
        cast = self.state.config.prikey_type
        if pk_value is not None and self._focus_row_by_prikey(pk_value):
            return
        pairs: list[tuple[int, int]] = []
        for i, r in enumerate(self.state.view_data):
            try:
                pairs.append((cast(r[prikey_field]), i))
            except Exception:
                continue
        if not pairs:
            self.state.selected_row_index = 0
            return
        pairs.sort(key=lambda x: x[0])
        keys = [k for k, _ in pairs]
        if pk_value is None:
            self.state.selected_row_index = pairs[0][1]
            return
        pos = bisect_left(keys, cast(pk_value))
        if pos < len(pairs):
            self.state.selected_row_index = pairs[pos][1]
        else:
            self.state.selected_row_index = pairs[-1][1]

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
                keep_pk = self._get_selected_prikey()
                self.state.filter_enabled = not self.state.filter_enabled
                self.state.apply_filter_and_sort()
                self._update_buffers()
                self._restore_focus_by_prikey_or_next(keep_pk)
                self._adjust_scroll()

        @kb_nav.add("s")
        def _(event):
            keep_pk = self._get_selected_prikey()
            self.state.sort_enabled = (self.state.sort_enabled + 1) % (len(self.state.config.sort_keys) + 1)
            self.state.apply_filter_and_sort()
            self._update_buffers()
            self._restore_focus_by_prikey_or_next(keep_pk)
            self._adjust_scroll()

        @kb_nav.add("r")
        def _(event):
            keep_pk = self._get_selected_prikey()
            self.state.load_data()
            self._update_buffers()
            self._restore_focus_by_prikey_or_next(keep_pk)
            self._adjust_scroll()

        @kb_nav.add("a")
        @kb_nav.add("o")
        def _(event):
            self._pending_delete = False
            self._add_row()

        @kb_nav.add("i")
        def _(event):
            self.state.show_id = not self.state.show_id
            prikey_field = self.state.config.prikey_field
            if (not self.state.show_id) and (self.state.headers[self.state.selected_col_index] == prikey_field):
                for h in self.state.headers:
                    if h != prikey_field and h not in self.state.config.generated_fields:
                        self.state.selected_col_index = self.state.headers.index(h)
                        break
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
        kf = self.state.config.prikey_field

        if not self.state.view_data:
            new_key = 1
        else:
            current_key = self.state.view_data[self.state.selected_row_index][kf]
            new_key = self.state.insert_key_position(current_key)

        if self.state.prikey_exists(new_key):
            self.logging_text = f"Add: computed {kf}={new_key} already exists (unexpected)."
            self.app.invalidate()
            return

        new_row = self.state.blank_row_dict(new_key)
        res = self.state.insert(new_row)
        self.logging_text = f"Add {res}: {kf}={new_key}"

        self._update_buffers()
        self._focus_row_by_prikey(new_key)
        self._adjust_scroll()

    def _start_editing(self):
        header = self.state.headers[self.state.selected_col_index]
        if header in self.state.config.generated_fields:
            self.logging_text = f"Edit: '{header}' column is read-only."
            self.app.invalidate()
            return
        if header == self.state.config.prikey_field and not self.state.config.allow_edit_prikey:
            self.logging_text = f"Edit: '{header}' is not editable."
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

        prikey_field = self.state.config.prikey_field
        stable_old_key = self.state.config.prikey_type(self.state.view_data[row_index][prikey_field])

        new_text = self.buffers[row_index][self.state.selected_col_index].text
        old_value = str(self.state.view_data[row_index].get(key, ""))

        if str(old_value) == str(new_text):
            self.logging_text = "Update: Not Change"
            self._update_layout()
            return

        track_key = stable_old_key
        if key == prikey_field:
            try:
                track_key = self.state.config.prikey_type(new_text)
            except ValueError:
                self.logging_text = "Update: primary key must be an integer."
                self._update_buffers()
                self._update_layout()
                return

        res = self.state.update(stable_old_key, {key: new_text})
        if not res:
            self.logging_text = self.state.info_text or "Update: Failed"
            self._update_buffers()
            self._update_layout()
            return

        self._update_buffers()

        found = self._focus_row_by_prikey(track_key)
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
        kf = self.state.config.prikey_field
        self.logging_text = f"Delete? {kf}={row[kf]} (press 'd' again to confirm, Esc to cancel)"
        self.app.invalidate()

    def _confirm_delete(self):
        if not self._pending_delete:
            return
        self._pending_delete = False
        row = self.state.view_data[self.state.selected_row_index]
        res = self.state.delete(row)
        kf = self.state.config.prikey_field
        self.logging_text = f"Delete {res}: {kf}={row[kf]}"
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
