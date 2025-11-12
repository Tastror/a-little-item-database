from scheme.genshin import genshin_scheme, genshin_init_data
from scheme.starrail import starrail_scheme, starrail_init_data
from db import Dataset, Column, VALUE


START = "\n" * 2 + "=" * 50 + " "
END = " " + "=" * 50 + "\n" * 2

print(START + "TEST 1" + END)

with Dataset(
    "game.db", "genshin_materials_just_for_test",
    create_scheme=genshin_scheme,
    create_data=genshin_init_data,
) as db:
    print(f"{db.head_name() = }")
    dq = db.dquery_all()
    print(f"{len(dq) = }")
    print(f"{dq[0] = }")
    print(f"{dq[1] = }")
    db._add_column(Column("hello", VALUE.REAL))
    db._rename_column("hello", "hi")
    db._delete_column("hi")
    db._rename_table("genshin_materials_just_for_test2")
    db._delete_table()


print(START + "TEST 2" + END)

with Dataset(
    "game.db", "starrail_materials_just_for_test",
    create_scheme=starrail_scheme,
    create_data=starrail_init_data,
) as db:
    print(f"{db.head_name() = }")
    print()

    lq = db.lquery_all()
    print(f"{len(lq) = }")
    print(f"{lq[0] = }")
    print(f"{lq[1] = }")
    print()

    db.store({'path': 123, 'position': 1, 'item_name': 2, 'tier1_count': 5})
    lq_2 = db.lquery_all()
    print(f"{len(lq_2) = }")
    print()

    dq_cons_1 = db.dquery_constrain({'position': 1})
    print(f"{len(dq_cons_1) = }")
    dq_cons_2 = db.dquery_constrain({'position': 1, 'tier1_count': 5})
    print(f"{len(dq_cons_2) = }")
    print(f"{dq_cons_2 = }")
    print()

    db.remove({'tier1_count': 5})
    dq_del = db.dquery_all()
    print(f"{len(dq_del) = }")
    print()

print("--- no create here ---")
with Dataset(
    "game.db", "starrail_materials_just_for_test",
) as db:
    db._delete_table()
