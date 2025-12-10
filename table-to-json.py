import sys
import json
from db import Dataset, Column, VALUE


# example: uv run table-to-json.py genshin_weapon

if __name__ == "__main__":
    name = sys.argv[1]
    with Dataset(
        "game.db", name,
    ) as db:
        dq = db.dquery_all()
    with open(f"{name}.json",'w') as f:
        f.write(json.dumps(dq, ensure_ascii=False))
        print(f"{name} table data wrote to {name}.json")
