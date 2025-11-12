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
    {'path': 'Destruction',     'position': 1,      'item_name': 'Worldbreaker Blade',      },
    {'path': 'Destruction',     'position': 2,      'item_name': 'Moon Rage Fang',          },
    {'path': 'The Hunt',        'position': 1,      'item_name': 'Arrow of the Starchaser', },
    {'path': 'The Hunt',        'position': 2,      'item_name': 'Countertemporal Shot',    },
    {'path': 'Erudition',       'position': 1,      'item_name': 'Key of Wisdom',           },
    {'path': 'Erudition',       'position': 2,      'item_name': 'Exquisite Colored Draft', },
    {'path': 'Preservation',    'position': 1,      'item_name': 'Safeguard of Amber',      },
    {'path': 'Preservation',    'position': 2,      'item_name': 'Divine Amber',            },
    {'path': 'Nihility',        'position': 1,      'item_name': 'Obsidian of Obsession',   },
    {'path': 'Nihility',        'position': 2,      'item_name': 'Heaven Incinerator',      },
    {'path': 'Harmony',         'position': 1,      'item_name': 'Stellaris Symphony'       },
    {'path': 'Harmony',         'position': 2,      'item_name': 'Heavenly Melody',         },
    {'path': 'Abundance',       'position': 1,      'item_name': 'Flower of Eternity',      },
    {'path': 'Abundance',       'position': 2,      'item_name': 'Myriad Fruit',            },
    {'path': 'Remembrance',     'position': 1,      'item_name': 'Flower of Ālaya',         },
]


if __name__ == "__main__":
    print(f"{starrail_scheme}")
    print(f"{starrail_scheme}")
