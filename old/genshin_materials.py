import sys
import gettext  # TODO: 添加本地化（&调研最佳实践）
import sqlite3
import datetime
from typing import Any
from enum import Enum, auto

from craft import CraftItem


class InteractiveCLI:
    def __init__(self, db: Dataset):
        self.db = db

    def _prompt_for_enum(self, enum_class: type[Enum], prompt_text: str) -> Any:
        print(prompt_text)
        members = list(enum_class)
        for i, member in enumerate(members):
            print(f"  {i+1}. {member.name}")

        while True:
            try:
                choice = int(input(f"Enter a number (1-{len(members)}): "))
                if 1 <= choice <= len(members):
                    return members[choice - 1]
                else:
                    print(f"Invalid number. Please enter a number between 1 and {len(members)}.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    def _prompt_for_loots(self) -> list[int]:
        while True:
            try:
                counts_str = input("Enter the counts for Tier1, Tier2, Tier3 (e.g., 10, 5, 2): ")
                parts = [int(p.strip()) for p in counts_str.split(',')]
                if len(parts) > 3 or len(parts) == 0:
                    print("Please provide 1 to 3 numbers separated by commas.")
                    continue
                while len(parts) < 3:
                    parts.append(0)
                return parts
            except ValueError:
                print("Invalid input. Please enter numbers separated by commas (e.g., 10, 5, 2).")

    def print_all_materials(self):
        all_items = self.get_all_items()
        if not all_items:
            print("Database is empty. Please add some materials first.")
            print("-" * 60)
            return

        show_items = []
        for (country, open_day), item in all_items.items():
            show_items.append((item, country, open_day))

        show_items.sort(key=lambda x: int(x[0]))

        print(f"{'Country':<15} {'Item Name':<20}\t{'Counts (T1, T2, T3)':<25} {'Values':<20}")
        print("-" * 60)
        for item, country, open_day in show_items:
            print(f"{country.name + ' (' + open_day.name + ')':<15} {item}")
        print("-" * 60)

    def print_today_materials(self):
        now = datetime.datetime.now()
        today_weekday = now.weekday()
        if now.hour < 4: today_weekday = (today_weekday + 6) % 7

        print("-" * 60)
        day_map = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"}
        print(f"Today is {day_map[today_weekday]}. Showing available materials:")

        if today_weekday == 6:
            print("(All materials are available on Sunday)")
            today_keys = [self.OpenDay._1, self.OpenDay._2, self.OpenDay._3]
        else:
            today_key_index = (today_weekday % 3) + 1
            today_keys = [self.OpenDay(today_key_index)]

        all_items = self.get_all_items()
        if not all_items:
            print("Database is empty. Please add some materials first.")
            print("-" * 60)
            return

        today_items = []
        for (country, open_day), item in all_items.items():
            if open_day in today_keys:
                today_items.append((item, country, open_day))

        if not today_items:
            print("No materials found for today in the database.")
            print("-" * 60)
            return

        today_items.sort(key=lambda x: int(x[0]))

        print(f"{'Country':<15} {'Item Name':<20}\t{'Counts (T1, T2, T3)':<25} {'Values':<20}")
        print("-" * 60)
        for item, country, open_day in today_items:
            print(f"{country.name + ' (' + open_day.name + ')':<15} {item}")
        print("-" * 60)


    def add_or_update_material(self):
        print("\n--- Add/Update Material ---")
        country = self._prompt_for_enum(Dataset.Country, "Select a country:")
        open_day = self._prompt_for_enum(Dataset.OpenDay, "Select an open day group (e.g., _1 for Mon/Thu):")
        existing_item = self.db.get_item(country, open_day)
        new_name = ""
        new_loots = [0, 0, 0]
        if existing_item:
            print("-" * 30)
            print("Found an existing record. Press Enter to keep the current value.")
            print(f"Current Data: {country.name}, {open_day.name} -> {existing_item}")
            print("-" * 30)
            new_name = existing_item.name
            new_loots = existing_item.loots
        else:
            print("This is a new entry. Please provide the required information.")
        while True:
            prompt = f"Enter item name (current: '{new_name}') or press Enter to keep: " if existing_item else "Enter a new item name (e.g., 'Freedom'): "
            user_input_name = input(prompt).strip()
            
            if user_input_name:
                new_name = user_input_name
                break
            elif existing_item:
                break
            else:
                print("Item name is required for a new entry.")
        while True:
            prompt = f"Enter counts T1,T2,T3 (current: {new_loots}) or press Enter to keep: " if existing_item else "Enter counts for T1, T2, T3 (e.g., 10, 5, 2): "
            user_input_counts = input(prompt).strip()
            if not user_input_counts:
                if existing_item:
                    break
                else:
                    new_loots = [0, 0, 0]
                    break
            try:
                parts = [int(p.strip()) for p in user_input_counts.split(',')]
                if len(parts) != 3:
                    print("Please provide 1 to 3 numbers separated by commas.")
                    continue
                new_loots = parts
                break
            except ValueError:
                print("Invalid input. Please enter numbers separated by commas (e.g., 10, 5, 2).")
        final_item = CraftItem(*new_loots, name=new_name)
        self.db.store(country, open_day, final_item)

    def run(self):
        while True:
            print("\n----- Genshin Material Manager -----")
            print("1. Show Today's Materials")
            print("2. Show All Materials")
            print("3. Add / Update a Material")
            print("4. Exit")
            choice = input("Enter your choice (1-4): ")

            if choice == '1':
                self.db.print_today_materials()
            elif choice == '2':
                self.db.print_all_materials()
            elif choice == '3':
                self.add_or_update_material()
            elif choice == '4':
                print("Exiting the program. Goodbye!")
                sys.exit(0)
            else:
                print("Invalid choice. Please enter a number between 1 and 4.")


if __name__ == "__main__":
    with Dataset(dataset_name="genshin_materials.db") as db:
        cli = InteractiveCLI(db)
        cli.run()
