from scheme.genshin import genshin_scheme, genshin_init_data
from scheme.starrail import starrail_scheme, starrail_init_data
from db import Dataset, Column, VALUE

with Dataset(
    "game.db", "genshin_materials",
) as db:
    dq = db.dquery_all()
    print(f"{dq = }")
    db._rename_table("genshin_materials_backup")

with Dataset(
    "game.db", "starrail_materials",
) as db:
    dq = db.dquery_all()
    print(f"{dq = }")
    db._rename_table("starrail_materials_backup")
