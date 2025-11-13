from scheme.genshin import genshin_scheme, genshin_init_data
from scheme.starrail import starrail_scheme, starrail_init_data
from db import Dataset, Column, VALUE

with Dataset(
    "game.db", "genshin_materials_backup",
) as db:
    db._delete_table()

with Dataset(
    "game.db", "starrail_materials_backup",
) as db:
    db._delete_table()
