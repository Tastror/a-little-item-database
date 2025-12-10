import sys
from db import Dataset, Column, VALUE


# example: uv run delete-backup.py genshin_weapon

if __name__ == "__main__":
    name = sys.argv[1]
    with Dataset(
        "game.db", f"{name}_backup",
    ) as db:
        db._delete_table()
        print(f"{name}_backup table deleted")
    print(f"TIPS: you can mannually delete {name}_backup.json")
