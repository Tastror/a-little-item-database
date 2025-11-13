import sqlite3
from typing import Any
from enum import Enum, auto

from logger import logger # type: ignore


class VALUE(Enum):
    NULL = auto()
    TEXT = auto()
    INTEGER = auto()
    REAL = auto()
    BLOB = auto()

class CONSTRAIN(Enum):
    PRIMARY_KEY = auto()
    UNIQUE = auto()
    CHECK = auto()
    FOREIGN_KEY = auto()


class Column:
    def __init__(
        self,
        name: str, type: VALUE,
        *,
        default: Any = None, not_null: bool = False,
        primary: bool = False, unique: bool = False,
        check: str | None = None, collate: str | None = None,
        autoincrement: bool = False,
        foreign_key_ref: str | None = None,
    ):
        """
        default: should add `'` yourself if you need
        """
        self.name = name
        self.type = type
        self.default = default
        self.not_null = not_null
        self.primary = primary
        self.unique = unique
        self.check = check
        self.collate = collate
        self.autoincrement = autoincrement
        self.foreign_key_ref = foreign_key_ref

    def __str__(self):
        result = self.name + " "
        result += self.type.name + " "
        if self.default is not None:
            result += f"DEFAULT {self.default} "
        if self.not_null:
            result += f"NOT NULL "
        if self.primary:
            result += "PRIMARY KEY "
        if self.unique:
            result += "UNIQUE "
        if self.check is not None:
            result += f"CHECK ({self.check})"
        if self.collate is not None:
            result += f"COLLATE ({self.collate})"
        if self.autoincrement:
            result += "AUTOINCREMENT "
        if self.foreign_key_ref is not None:
            result += f"FOREIGN KEY REFERENCES ({self.foreign_key_ref})"
        return result[:-1]

class Constrain:
    def __init__(
        self,
        constrain_type: CONSTRAIN,
        _1: str | None = None,
        *,
        _2: str | None = None,
        _3: str | None = None,
        give_name: str | None = None,
    ):
        self.constrain_type = constrain_type
        self.give_name = give_name
        self._1 = _1
        self._2 = _2
        self._3 = _3

    def __str__(self) -> str:
        result = ""
        if self.give_name:
            result += f"CONSTRAINT {self.give_name} "
        if self.constrain_type == CONSTRAIN.PRIMARY_KEY:
            return result + f"PRIMARY KEY ({self._1})"
        elif self.constrain_type == CONSTRAIN.UNIQUE:
            return result + f"UNIQUE ({self._1})"
        elif self.constrain_type == CONSTRAIN.CHECK:
            return result + f"CHECK ({self._1})"
        elif self.constrain_type == CONSTRAIN.FOREIGN_KEY:
            return result + f"FOREIGN KEY ({self._1}) REFERENCES {self._2}"
        else:
            raise NotImplementedError(f"{self.constrain_type} is not implement")


class Scheme():

    def __init__(self):
        self.column_list: list[Column] = []
        self.constrain_list: list[Constrain] = []

    def add_column(self, column: Column):
        self.column_list.append(column)

    def add_columns(self, columns: list[Column]):
        self.column_list.extend(columns)

    def add_constrain(self, constrain: Constrain):
        self.constrain_list.append(constrain)

    def add_constrains(self, constrains: list[Constrain]):
        self.constrain_list.extend(constrains)

    def rename_column(self, old_name: str, new_name: str) -> bool:
        for col in self.column_list:
            if col.name == old_name:
                col.name = new_name
                return True
        return False

    def delete_column(self, col_name: str) -> bool:
        for i, col in enumerate(self.column_list):
            if col.name == col_name:
                del self.column_list[i]
                return True
        else:
            return False

    def head(self) -> list[ Column | Constrain ]:
        return self.column_list + self.constrain_list

    def __str__(self) -> str:
        head = self.head()
        if len(head) == 0: return "()"
        result = "("
        for co in head:
            result += f"\n    {co},"
        return result[:-1] + "\n)"


class Dataset:

    def __init__(
        self, dataset_name: str, table_name: str,
        *,
        create_scheme: Scheme | None = None,
        create_data: list[dict] | None = None,
    ):
        self.db_name = dataset_name
        self.table_name = table_name
        self.create_scheme = create_scheme
        self.create_data = create_data
        self.conn: sqlite3.Connection | None = None
        self.cursor: sqlite3.Cursor | None = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?", (self.table_name,))
        table_exists = self.cursor.fetchone() is not None
        if not table_exists:
            if self.create_scheme is None:
                raise ValueError(f"{self.table_name} is not exist, so create_scheme must be specified")
            self._create_table()
            if self.create_data is not None:
                self.store_many(self.create_data)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        if self.conn:
            self.conn.commit()
            self.conn.close()

    @staticmethod
    def precheck(func):
        def wrapper(self, *args, **kwargs):
            if not self.cursor:
                logger.warning(f"<{self.table_name}>: cursor is not available")
                return
            return func(self, *args, **kwargs)
        return wrapper

    @staticmethod
    def precheck_return(return_data):
        def deco(func):
            def wrapper(self, *args, **kwargs):
                if not self.cursor:
                    logger.warning(f"<{self.table_name}>: cursor is not available")
                    return return_data
                return func(self, *args, **kwargs)
            return wrapper
        return deco

    @precheck
    def _create_table(self):
        assert self.cursor is not None  # just to suppress type error
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.table_name} {self.create_scheme}")
        logger.info(f"<{self.table_name}>: create table")

    @precheck
    def _add_column(self, column: Column):
        assert self.cursor is not None
        self.cursor.execute(f"ALTER TABLE {self.table_name} ADD COLUMN {column}")
        logger.info(f"<{self.table_name}>: add column {column}")

    @precheck
    def _rename_table(self, new_name: str):
        assert self.cursor is not None
        old_name = self.table_name
        self.cursor.execute(f"ALTER TABLE {old_name} RENAME TO {new_name}")
        self.table_name = new_name
        logger.info(f"<{self.table_name}>: rename table {old_name} > {new_name}")

    @precheck
    def _rename_column(self, old_name: str, new_name: str):
        assert self.cursor is not None
        self.cursor.execute(f"ALTER TABLE {self.table_name} RENAME COLUMN {old_name} TO {new_name}")
        logger.info(f"<{self.table_name}>: rename column {old_name} > {new_name}")

    @precheck
    def _delete_column(self, col_name: str):
        assert self.cursor is not None
        self.cursor.execute(f"ALTER TABLE {self.table_name} DROP COLUMN {col_name}")
        logger.info(f"<{self.table_name}>: delete column {col_name}")

    @precheck
    def _delete_table(self):
        assert self.cursor is not None
        self.cursor.execute(f"DROP TABLE IF EXISTS {self.table_name}")
        logger.info(f"<{self.table_name}>: delete table")

    @precheck_return([])
    def head(self) -> list[tuple]:
        assert self.cursor is not None
        self.cursor.execute(f"PRAGMA table_info({self.table_name})")
        res = self.cursor.fetchall()
        logger.info(f"<{self.table_name}>: head queried")
        return res

    def head_name(self) -> list[str]:
        head = []
        for i in self.head():
            head.append(i[1])
        return head

    @precheck_return([])
    def lquery_constrain(self, constrain_dict: dict) -> list[tuple]:
        assert self.cursor is not None
        where = " AND ".join([i + " = ?" for i in constrain_dict.keys()])
        query = f"SELECT * FROM {self.table_name} WHERE {where}"
        self.cursor.execute(query, tuple(constrain_dict.values()))
        res = self.cursor.fetchall()
        logger.info(f"<{self.table_name}>: all queried")
        return res

    def dquery_constrain(self, constrain_dict: dict) -> list[dict]:
        res = self.lquery_constrain(constrain_dict)
        head = self.head_name()
        res = [dict(zip(head, row)) for row in res]
        return res

    @precheck_return([])
    def lquery_all(self) -> list[tuple]:
        assert self.cursor is not None
        query = f"SELECT * FROM {self.table_name}"
        self.cursor.execute(query)
        res = self.cursor.fetchall()
        logger.info(f"<{self.table_name}>: all queried")
        return res

    def dquery_all(self) -> list[dict]:
        res = self.lquery_all()
        head = self.head_name()
        res = [dict(zip(head, row)) for row in res]
        return res

    @precheck_return(False)
    def store(self, item: dict) -> bool:
        assert self.cursor is not None
        if not item:
            logger.warning(f"<{self.table_name}>: store is empty")
            return True
        keys = tuple(item.keys())
        values = tuple(item.values())
        cols_str = ", ".join(keys)
        placeholders = ", ".join(["?"] * len(keys))
        query = f"INSERT OR REPLACE INTO {self.table_name} ({cols_str}) VALUES ({placeholders})"
        self.cursor.execute(query, values)
        logger.info(f"<{self.table_name}>: {item} stored")
        return True

    @precheck_return(False)
    def store_many(self, items: list[dict]) -> bool:
        assert self.cursor is not None
        if not items:
            logger.warning(f"<{self.table_name}>: store is empty")
            return True
        try:
            keys = tuple(items[0].keys())
        except (IndexError, AttributeError):
            logger.error(f"<{self.table_name}>: {items = } must be a non-empty list of dictionaries")
            return False
        cols_str = ", ".join(f'"{k}"' for k in keys)
        placeholders = ", ".join(["?"] * len(keys))
        query = f"INSERT OR REPLACE INTO {self.table_name} ({cols_str}) VALUES ({placeholders})"
        try:
            values_list = [tuple(item.get(k) for k in keys) for item in items]
        except AttributeError:
            logger.error(f"<{self.table_name}>: {items = } all elements must be dictionaries.")
            return False
        self.cursor.executemany(query, values_list)
        logger.info(f"<{self.table_name}>: {len(items)} item(s) stored")
        return True

    def remove(self, delete_dict: dict) -> bool:
        assert self.cursor is not None
        if not delete_dict or len(delete_dict) == 0:
            logger.warning(f"<{self.table_name}>: won't delete if not specified")
            return False
        where = " AND ".join([i + " = ?" for i in delete_dict.keys()])
        query = f"DELETE FROM {self.table_name} WHERE {where}"
        self.cursor.execute(query, tuple(delete_dict.values()))
        logger.info(f"<{self.table_name}>: {delete_dict} deleted")
        return True

    def insert_or_update(self, item: dict) -> bool:
        return self.store(item)

    def delete(self, delete_dict: dict) -> bool:
        return self.remove(delete_dict)
