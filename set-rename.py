from db import Dataset, Column, VALUE

with Dataset(
    "game.db", "genshin_materials",
) as db:
    dq = db.dquery_all()
    print(f"{dq = }")
    db._rename_table("genshin_materials_backup")

with Dataset(
    "game.db", "genshin_weapon",
) as db:
    dq = db.dquery_all()
    print(f"{dq = }")
    db._rename_table("genshin_weapon_backup")

with Dataset(
    "game.db", "starrail_materials",
) as db:
    dq = db.dquery_all()
    print(f"{dq = }")
    db._rename_table("starrail_materials_backup")
