from db import SQLITE_TYPE, CONSTRAIN_TYPE, Column, Constrain, Scheme

genshin_scheme = Scheme()
genshin_scheme.add_columns([
    Column("country", SQLITE_TYPE.TEXT),
    Column("open_day", SQLITE_TYPE.INTEGER),
    Column("item_name", SQLITE_TYPE.INTEGER),
    Column("tier1_count", SQLITE_TYPE.INTEGER, default=0),
    Column("tier2_count", SQLITE_TYPE.INTEGER, default=0),
    Column("tier3_count", SQLITE_TYPE.INTEGER, default=0),
])
genshin_scheme.add_constrain(
    Constrain(CONSTRAIN_TYPE.PRIMARY_KEY, "country, open_day")
)

genshin_init_data = [
    {'country': 'Mondstadt',    'open_day': 1,      'item_name': 'Freedom',      },
    {'country': 'Mondstadt',    'open_day': 2,      'item_name': 'Resistance',   },
    {'country': 'Mondstadt',    'open_day': 3,      'item_name': 'Ballad',       },
    {'country': 'Liyue',        'open_day': 1,      'item_name': 'Prosperity',   },
    {'country': 'Liyue',        'open_day': 2,      'item_name': 'Diligence',    },
    {'country': 'Liyue',        'open_day': 3,      'item_name': 'Gold'          },
    {'country': 'Inazuma',      'open_day': 1,      'item_name': 'Transience',   },
    {'country': 'Inazuma',      'open_day': 2,      'item_name': 'Elegance',     },
    {'country': 'Inazuma',      'open_day': 3,      'item_name': 'Light'         },
    {'country': 'Sumeru',       'open_day': 1,      'item_name': 'Admonition',   },
    {'country': 'Sumeru',       'open_day': 2,      'item_name': 'Ingenuity',    },
    {'country': 'Sumeru',       'open_day': 3,      'item_name': 'Praxis',       },
    {'country': 'Fontaine',     'open_day': 1,      'item_name': 'Equity',       },
    {'country': 'Fontaine',     'open_day': 2,      'item_name': 'Justice',      },
    {'country': 'Fontaine',     'open_day': 3,      'item_name': 'Order'         },
    {'country': 'Natlan',       'open_day': 1,      'item_name': 'Contention',   },
    {'country': 'Natlan',       'open_day': 2,      'item_name': 'Kindling',     },
    {'country': 'Natlan',       'open_day': 3,      'item_name': 'Conflict',     },
    {'country': 'Nod_Krai',     'open_day': 1,      'item_name': 'Moonlight',    },
    {'country': 'Nod_Krai',     'open_day': 2,      'item_name': 'Elysium',      },
    {'country': 'Nod_Krai',     'open_day': 3,      'item_name': 'Vagrancy',     },
]


if __name__ == "__main__":
    print(f"{genshin_scheme}")
    print(f"{genshin_init_data}")
