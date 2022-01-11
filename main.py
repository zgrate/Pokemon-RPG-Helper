import os.path
from threading import Thread
from time import sleep
from typing import Optional

import jsonpickle

import level_generator
from ConsoleMenu import ConsoleMenu
from battle_scripts import encounter, get_team, wait_for_click, get_max_hp, get_hp, heal_pokemon_from_console, \
    pokemon_menu
from classes import PokemonWithStats
from data_access import get_pokemon
from level_generator import navigate_floor

# a = json.load(open("types.json", "r"))
# request = requests.get('https://pokeapi.co/api/v2/type/1/')

team = [PokemonWithStats("Zarion", 40, get_pokemon("absol", "super luck", ["dark"],
                                                   ["dark pulse", "thunder", "future sight", "dream eater"])),
        PokemonWithStats("Lax", 40, get_pokemon("lycanroc-midday", "fairy aura", ["fairy", "rock"],
                                                ["moonblast", "bite", "charm", "moonlight"])),
        PokemonWithStats("Glossy", 40, get_pokemon("vaporeon", "drizzle", ["fairy", "water"],
                                                   ["hydro pump", "moonblast", "blizzard", "tickle"])),
        PokemonWithStats("Fenice", 40,
                         get_pokemon("luxray", "guts", ["electric"], ["crunch", "thunder", "rest", "spark"]))
        ]


# print(team)




def hp_heal_team():
    for t in team:
        heal_pokemon_from_console("100%", t)


def team_reset():
    for t in team:
        t.reset_stats_changes()
        t.reset_status_effects()
        heal_pokemon_from_console("100%", t)


def team_action():
    return ConsoleMenu("What to do as a team?", {
        "HP Heal": hp_heal_team,
        "Full heal": team_reset
    })


def open_team():
    print(get_team(team))
    a = {}
    for pkmn in team:
        a[f"{pkmn.name} ({get_hp(pkmn)}/{get_max_hp(pkmn)})"] = pkmn
    a["Team Actions"] = "team"

    response = wait_for_click("Details: ", a)
    if response is None:
        return "back"
    elif response == "team":
        return team_action()
    else:
        return pokemon_menu(response)


current_floor: Optional[dict] = None


def new_floor():
    try:
        types = input("Type in types on the floor. Comma-separated. ")
        global current_floor
        current_floor = level_generator.generate_floor(types.split(","))

    except KeyboardInterrupt:
        return


def floor_options():
    return ConsoleMenu("Floors:", {
        f"Generate new (Now it's {'generated' if current_floor else 'not generated'})": new_floor,
        "Dungeon details: ": lambda: navigate_floor(current_floor)
    })


def save_all(target="save_data.json"):
    to_save_data = {
        "team": team,
        "current_battle": current_battle,
        "current_floor": current_floor
    }
    with open(target, "w", encoding="utf-8") as save_file:
        save_file.write(jsonpickle.encode(to_save_data, indent=4))


def load_all(target="save_data.json"):
    if os.path.exists(target):
        with open(target, "r", encoding="utf-8") as load_file:
            loaded_data = jsonpickle.decode(load_file.read())
            global team, current_battle, current_floor
            team = loaded_data["team"]
            current_battle = loaded_data["current_battle"]
            current_floor = loaded_data["current_floor"]


current_battle = {
    "second_pokemon": None,
    "first_pokemon": None,
    "turn": 1,
    "first_switched": False,
    "second_switched": False
}

load_all()


def save():
    while True:
        save_all()
        sleep(10)


if __name__ == "__main__":

    try:
        Thread(target=save, daemon=True).start()

        m = ConsoleMenu("Test", {
            "Team": open_team,
            "Encounter": lambda: encounter(team, current_battle),
            "Dungeon": floor_options
        })
        m.execute()
    except KeyboardInterrupt:
        save_all()

# # print(get_move_data("acid-armor"))
# print(fight(team[0], team[1], get_move_data("thunder")))
# print("\n--------------------------\n")
# print(get_pokemon_stats_formatted(team[1]))
