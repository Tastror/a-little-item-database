import sys
import json
from pathlib import Path

import scheme.genshin, scheme.starrail
from db import Dataset, Column, VALUE


# example: uv run json-to-table.py genshin_weapon

if __name__ == "__main__":
    name = sys.argv[1]
    name_with_json = Path(name) if name.endswith(".json") else Path(f"{name}.json")
    table_name = name_with_json.stem

    if not name_with_json.exists():
        print(f"file {name_with_json} does not exist")
        exit(1)

    if table_name.startswith("genshin_materials"):
        create_scheme = scheme.genshin.genshin_scheme
        create_data = scheme.genshin.genshin_init_data
    elif table_name.startswith("genshin_weapon"):
        create_scheme = scheme.genshin.genshin_weapon_scheme
        create_data = scheme.genshin.genshin_weapon_init_data
    elif table_name.startswith("starrail_materials"):
        create_scheme = scheme.starrail.starrail_scheme
        create_data = scheme.starrail.starrail_init_data
    else:
        print(f"cannot find proper scheme for table {table_name}")
        exit(1)

    with open(name_with_json,'r') as f:
        table_new_data = json.loads(f.read())
        print(f"{name_with_json} read")

    backup = table_name + "_backup"
    with Dataset(
        "game.db", table_name,
    ) as db:
        dq = db.dquery_all()
        with open(f"{backup}.json",'w') as f:
            f.write(json.dumps(dq, ensure_ascii=False))
            print(f"{table_name} table data backup to {backup}.json and rename to {backup}")
        db._rename_table(backup)

    with Dataset(
        "game.db", table_name,
        create_scheme=create_scheme,
        create_data=create_data,
    ) as db:
        print(db.head_name())
        for data in table_new_data:
            # may_have = db.dquery_constrain({
            #     "country": data["country"],
            #     "open_day": data["open_day"]
            # })
            # if len(may_have) == 1:
            #     data["id"] = may_have[0]["id"]
            db.store(data)
        print(f"data stored in {table_name}")
