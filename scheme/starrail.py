from db import SQLITE_TYPE, CONSTRAIN_TYPE, Column, Constrain, Scheme

starrail_scheme = Scheme()
starrail_scheme.add_columns([
    Column("path", SQLITE_TYPE.TEXT),
    Column("position", SQLITE_TYPE.INTEGER),
    Column("item_name", SQLITE_TYPE.INTEGER),
    Column("tier1_count", SQLITE_TYPE.INTEGER, default=0),
    Column("tier2_count", SQLITE_TYPE.INTEGER, default=0),
    Column("tier3_count", SQLITE_TYPE.INTEGER, default=0),
])
starrail_scheme.add_constrain(
    Constrain(CONSTRAIN_TYPE.PRIMARY_KEY, "path, position")
)

starrail_init_data = [
    {'path': 'Mondstadt',    'position': 1,      'item_name': 'Freedom',      },
    {'path': 'Mondstadt',    'position': 2,      'item_name': 'Resistance',   },
    {'path': 'Mondstadt',    'position': 3,      'item_name': 'Ballad',       },
    {'path': 'Liyue',        'position': 1,      'item_name': 'Prosperity',   },
    {'path': 'Liyue',        'position': 2,      'item_name': 'Diligence',    },
    {'path': 'Liyue',        'position': 3,      'item_name': 'Gold'          },
    {'path': 'Inazuma',      'position': 1,      'item_name': 'Transience',   },
    {'path': 'Inazuma',      'position': 2,      'item_name': 'Elegance',     },
    {'path': 'Inazuma',      'position': 3,      'item_name': 'Light'         },
    {'path': 'Sumeru',       'position': 1,      'item_name': 'Admonition',   },
    {'path': 'Sumeru',       'position': 2,      'item_name': 'Ingenuity',    },
    {'path': 'Sumeru',       'position': 3,      'item_name': 'Praxis',       },
    {'path': 'Fontaine',     'position': 1,      'item_name': 'Equity',       },
    {'path': 'Fontaine',     'position': 2,      'item_name': 'Justice',      },
    {'path': 'Fontaine',     'position': 3,      'item_name': 'Order'         },
    {'path': 'Natlan',       'position': 1,      'item_name': 'Contention',   },
    {'path': 'Natlan',       'position': 2,      'item_name': 'Kindling',     },
    {'path': 'Natlan',       'position': 3,      'item_name': 'Conflict',     },
    {'path': 'Nod_Krai',     'position': 1,      'item_name': 'Moonlight',    },
    {'path': 'Nod_Krai',     'position': 2,      'item_name': 'Elysium',      },
    {'path': 'Nod_Krai',     'position': 3,      'item_name': 'Vagrancy',     },
]


if __name__ == "__main__":
    print(f"{starrail_scheme}")
    print(f"{starrail_scheme}")
