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
    {"country": "Mondstadt",    "open_day": 1,      "item_name": "Scattered Piece of Decarabian's Dream",       },
    {"country": "Mondstadt",    "open_day": 2,      "item_name": "Boreal Wolf's Nostalgia",                     },
    {"country": "Mondstadt",    "open_day": 3,      "item_name": "Dream of the Dandelion Gladiator",            },
    {"country": "Liyue",        "open_day": 1,      "item_name": "Divine Body from Guyun",                      },
    {"country": "Liyue",        "open_day": 2,      "item_name": "Mist Veiled Primo Elixir",                    },
    {"country": "Liyue",        "open_day": 3,      "item_name": "Chunk of Aerosiderite"                        },
    {"country": "Inazuma",      "open_day": 1,      "item_name": "Golden Branch of a Distant Sea",              },
    {"country": "Inazuma",      "open_day": 2,      "item_name": "Narukami's Valor",                            },
    {"country": "Inazuma",      "open_day": 3,      "item_name": "Mask of the Kijin"                            },
    {"country": "Sumeru",       "open_day": 1,      "item_name": "Golden Talisman of the Forest Dew",           },
    {"country": "Sumeru",       "open_day": 2,      "item_name": "Oasis Garden's Truth",                        },
    {"country": "Sumeru",       "open_day": 3,      "item_name": "Olden Days of Scorching Might",               },
    {"country": "Fontaine",     "open_day": 1,      "item_name": "Echo of an Ancient Chord",                    },
    {"country": "Fontaine",     "open_day": 2,      "item_name": "Essence of Pure Sacred Dewdrop",              },
    {"country": "Fontaine",     "open_day": 3,      "item_name": "Golden Goblet of the Pristine Sea"            },
    {"country": "Natlan",       "open_day": 1,      "item_name": "Blazing Sacrificial Heart's Splendor",        },
    {"country": "Natlan",       "open_day": 2,      "item_name": "Delirious Divinity of the Sacred Lord",       },
    {"country": "Natlan",       "open_day": 3,      "item_name": "Night-Wind's Mystic Revelation",              },
    {"country": "Nod_Krai",     "open_day": 1,      "item_name": "Artful Device Wish",                          },
    {"country": "Nod_Krai",     "open_day": 2,      "item_name": "Blaze of Long Night Flint",                   },
    {"country": "Nod_Krai",     "open_day": 3,      "item_name": "Aureate Radiance of the Far-North Scions",    },
]



if __name__ == "__main__":
    print(f"{genshin_scheme}")
    print(f"{genshin_init_data}")
    print(f"{genshin_weapon_scheme}")
    print(f"{genshin_weapon_init_data}")
