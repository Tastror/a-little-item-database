import scheme.genshin, scheme.starrail
from db import Dataset, Column, VALUE

genshin_insert_data = []

genshin_weapon_insert_data = []

starrail_insert_data = []

with Dataset(
    "game.db", "genshin_materials",
    create_scheme=scheme.genshin.genshin_scheme,
    create_data=scheme.genshin.genshin_init_data,
) as db:
    print(db.head_name())
    for data in genshin_insert_data:
        may_have = db.dquery_constrain({
            "country": data["country"],
            "open_day": data["open_day"]
        })
        if len(may_have) == 1:
            data["id"] = may_have[0]["id"]  # replace
        db.store(data)
    dq = db.dquery_all()
    print(f"{dq = }")

with Dataset(
    "game.db", "genshin_weapon",
    create_scheme=scheme.genshin.genshin_weapon_scheme,
    create_data=scheme.genshin.genshin_weapon_init_data,
) as db:
    print(db.head_name())
    for data in genshin_weapon_insert_data:
        may_have = db.dquery_constrain({
            "country": data["country"],
            "open_day": data["open_day"]
        })
        if len(may_have) == 1:
            data["id"] = may_have[0]["id"]  # replace
        db.store(data)
    dq = db.dquery_all()
    print(f"{dq = }")

with Dataset(
    "game.db", "starrail_materials",
    create_scheme=scheme.starrail.starrail_scheme,
    create_data=scheme.starrail.starrail_init_data,
) as db:
    print(db.head_name())
    for data in starrail_insert_data:
        may_have = db.dquery_constrain({
            "country": data["country"],
            "open_day": data["open_day"]
        })
        if len(may_have) == 1:
            data["id"] = may_have[0]["id"]
        db.store(data)
    dq = db.dquery_all()
    print(f"{dq = }")
