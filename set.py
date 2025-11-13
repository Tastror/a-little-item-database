from scheme.genshin import genshin_scheme, genshin_init_data
from scheme.starrail import starrail_scheme, starrail_init_data
from db import Dataset, Column, VALUE

genshin_insert_data = []

starrail_insert_data = []

with Dataset(
    "game.db", "genshin_materials",
    create_scheme=genshin_scheme,
    create_data=genshin_init_data,
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
    "game.db", "starrail_materials",
    create_scheme=starrail_scheme,
    create_data=starrail_init_data,
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
