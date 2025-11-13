from db import VALUE, CONSTRAIN, Column, Constrain, Scheme

genshin_scheme = Scheme()
genshin_scheme.add_columns([
    Column("id", VALUE.INTEGER, primary=True, autoincrement=True),
    Column("country", VALUE.TEXT),
    Column("open_day", VALUE.INTEGER),
    Column("item_name", VALUE.TEXT),
    Column("tier1_count", VALUE.INTEGER, default=0),
    Column("tier2_count", VALUE.INTEGER, default=0),
    Column("tier3_count", VALUE.INTEGER, default=0),
])

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



genshin_weapon_scheme = Scheme()
genshin_weapon_scheme.add_columns([
    Column("id", VALUE.INTEGER, primary=True, autoincrement=True),
    Column("country", VALUE.TEXT),
    Column("open_day", VALUE.INTEGER),
    Column("item_name", VALUE.TEXT),
    Column("tier1_count", VALUE.INTEGER, default=0),
    Column("tier2_count", VALUE.INTEGER, default=0),
    Column("tier3_count", VALUE.INTEGER, default=0),
    Column("tier4_count", VALUE.INTEGER, default=0),
])

genshin_weapon_init_data = [
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
    print(f"{genshin_weapon_scheme}")
    print(f"{genshin_weapon_init_data}")
