from scheme.genshin import genshin_scheme, genshin_init_data
from scheme.starrail import starrail_scheme, starrail_init_data
from db import Dataset, Column, VALUE

genshin_insert_data = [{'country': 'Mondstadt', 'open_day': 2, 'item_name': 'Resistance', 'tier1_count': 17, 'tier2_count': 49, 'tier3_count': 57}, {'country': 'Mondstadt', 'open_day': 3, 'item_name': 'Ballad', 'tier1_count': 18, 'tier2_count': 68, 'tier3_count': 89}, {'country': 'Liyue', 'open_day': 1, 'item_name': 'Prosperity', 'tier1_count': 19, 'tier2_count': 52, 'tier3_count': 110}, {'country': 'Liyue', 'open_day': 2, 'item_name': 'Diligence', 'tier1_count': 33, 'tier2_count': 178, 'tier3_count': 209}, {'country': 'Liyue', 'open_day': 3, 'item_name': 'Gold', 'tier1_count': 23, 'tier2_count': 55, 'tier3_count': 204}, {'country': 'Mondstadt', 'open_day': 1, 'item_name': 'Freedom', 'tier1_count': 23, 'tier2_count': 52, 'tier3_count': 38}, {'country': 'Inazuma', 'open_day': 2, 'item_name': 'Elegance', 'tier1_count': 23, 'tier2_count': 26, 'tier3_count': 120}, {'country': 'Inazuma', 'open_day': 3, 'item_name': 'Light', 'tier1_count': 13, 'tier2_count': 79, 'tier3_count': 120}, {'country': 'Sumeru', 'open_day': 1, 'item_name': 'Admonition', 'tier1_count': 58, 'tier2_count': 208, 'tier3_count': 221}, {'country': 'Sumeru', 'open_day': 2, 'item_name': 'Ingenuity', 'tier1_count': 58, 'tier2_count': 242, 'tier3_count': 222}, {'country': 'Sumeru', 'open_day': 3, 'item_name': 'Praxis', 'tier1_count': 37, 'tier2_count': 231, 'tier3_count': 268}, {'country': 'Fontaine', 'open_day': 2, 'item_name': 'Justice', 'tier1_count': 40, 'tier2_count': 67, 'tier3_count': 95}, {'country': 'Fontaine', 'open_day': 3, 'item_name': 'Order', 'tier1_count': 61, 'tier2_count': 182, 'tier3_count': 227}, {'country': 'Natlan', 'open_day': 2, 'item_name': 'Kindling', 'tier1_count': 25, 'tier2_count': 60, 'tier3_count': 121}, {'country': 'Natlan', 'open_day': 3, 'item_name': 'Conflict', 'tier1_count': 51, 'tier2_count': 167, 'tier3_count': 249}, {'country': 'Nod_Krai', 'open_day': 2, 'item_name': 'Elysium', 'tier1_count': 3, 'tier2_count': 65, 'tier3_count': 56}, {'country': 'Nod_Krai', 'open_day': 3, 'item_name': 'Vagrancy', 'tier1_count': 7, 'tier2_count': 66, 'tier3_count': 60}, {'country': 'Inazuma', 'open_day': 1, 'item_name': 'Transience', 'tier1_count': 18, 'tier2_count': 36, 'tier3_count': 96}, {'country': 'Nod_Krai', 'open_day': 1, 'item_name': 'Moonlight', 'tier1_count': 11, 'tier2_count': 75, 'tier3_count': 81}, {'country': 'Natlan', 'open_day': 1, 'item_name': 'Contention', 'tier1_count': 12, 'tier2_count': 67, 'tier3_count': 60}, {'country': 'Fontaine', 'open_day': 1, 'item_name': 'Equity', 'tier1_count': 37, 'tier2_count': 211, 'tier3_count': 273}]

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
