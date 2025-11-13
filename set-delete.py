from db import Dataset, Column, VALUE

with Dataset(
    "game.db", "genshin_materials_backup",
) as db:
    db._delete_table()

with Dataset(
    "game.db", "genshin_weapon_backup",
) as db:
    db._delete_table()

with Dataset(
    "game.db", "starrail_materials_backup",
) as db:
    db._delete_table()
