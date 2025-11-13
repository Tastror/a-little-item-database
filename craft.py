class CraftItem:

    CRAFT_CONST = 3

    def __init__(
        self,
        *loots: int | list | tuple,
        name: str = "Anonymous-Item", only_eqv: bool = False
    ) -> None:
        self.name: str = name
        self.only_eqv = only_eqv
        self.loots: list[int] = []
        self.set_loots(*loots)

    def set_loots(self, *loots: int | list | tuple) -> None:
        if len(loots) == 1 and isinstance(loots[0], (tuple, list)):
            self.loots = list(loots[0])
            print("Warning: better to make the loots split by ',' instead of passing a tuple or list")
        else:
            self.loots = list(loots)  # type: ignore
        while len(self.loots) < 3:
            self.loots.append(0)
        self.loots = self.loots[:3]
        for i, data in enumerate(self.loots):
            try: int(data)
            except: self.loots[i] = 0

    def __int__(self) -> int:
        total = 0
        multiplier = 1
        for loot in reversed(self.loots):
            total += loot * multiplier
            multiplier *= self.CRAFT_CONST
        return total

    def __float__(self) -> float:
        total = 0
        multiplier = 1
        for loot in self.loots:
            total += loot / multiplier
            multiplier *= self.CRAFT_CONST
        return total

    def __lt__(self, other: 'CraftItem') -> bool:
        return int(self) < int(other)

    def __str__(self) -> str:
        if self.only_eqv:
            return f"{float(self):.2f} ({int(self)})"
        return (
            f"{self.name:<20}\t"
            f"[{self.loots[0]:>3}, {self.loots[1]:>3}, {self.loots[2]:>3}];\t"
            f"(Eqv. Big:{float(self):>7.2f}, Small:{int(self):>5})"
        )
