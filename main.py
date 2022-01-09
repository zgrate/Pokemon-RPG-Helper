import os.path
from threading import Thread
from time import sleep
from typing import Optional

import jsonpickle

import calculations
import classes
import level_generator
from ConsoleMenu import ConsoleMenu
from battle_scripts import get_pokemon_stats_formatted, encounter, get_team, wait_for_click, get_max_hp, heal_pokemon, \
    damage_pokemon, get_hp
from calculations import get_stat
from classes import PokemonWithStats, ATTACK, DEFENSE, SP_ATTACK, SP_DEFENSE, SPEED
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


def heal_pokemon_from_console(value: str, pokemon: PokemonWithStats):
    if value is None:
        return
    if "%" in value:
        percentage = float(value[:-1]) / 100
        heal_pokemon(pokemon, get_max_hp(pokemon) * percentage)
    else:
        heal_pokemon(pokemon, int(value))


def damage_pokemon_from_console(value: str, pokemon: PokemonWithStats):
    if value is None:
        return
    if "%" in value:
        percentage = float(value[:-1]) / 100
        damage_pokemon(pokemon, get_max_hp(pokemon) * percentage)
    else:
        damage_pokemon(pokemon, int(value))


def edit_stat(stat: str, pokemon: PokemonWithStats):
    try:
        if stat == "hp":
            value = wait_for_click("Heal of damage?",
                                   {"Heal": "heal", "Damage": "damage", "Faint": "faint", "Respawn": "respawn",
                                    "Full heal": "full_heal"})
            if value is None:
                return
            match value:
                case "heal":
                    value = input("How much HP should you heal pokemon? You can use percentage or value")
                    heal_pokemon_from_console(value, pokemon)
                case "damage":
                    value = input("How much damage do you want to deal your pokemon? You can use percentage or value")
                    damage_pokemon_from_console(value, pokemon)
                case "faint":
                    damage_pokemon_from_console("100%", pokemon)
                case "respawn":
                    heal_pokemon_from_console("50%", pokemon)
                case "full_heal":
                    heal_pokemon_from_console("100%", pokemon)

            if calculations.fainted(pokemon):
                print(f"{pokemon.name} fainted!")

            if value == "max":
                pokemon.stats_changes.hp = 0


        else:
            value = int(input(f"Type new value for {stat.capitalize()} "))
            match stat:
                case classes.ATTACK:
                    pokemon.stats_changes.attack = value
                case classes.DEFENSE:
                    pokemon.stats_changes.defense = value
                case classes.SP_ATTACK:
                    pokemon.stats_changes.special_attack = value
                case classes.SP_DEFENSE:
                    pokemon.stats_changes.special_defense = value
                case classes.SPEED:
                    pokemon.stats_changes.speed = value
                case "acc":
                    pokemon.stats_changes.accuracy = value
                case "evs":
                    pokemon.stats_changes.evasiveness = value
                case "crit":
                    pokemon.stats_changes.critical = value

            print(f"New value for {stat.capitalize()} is {value}")


    except Exception:
        print("Cancelled")
        return

    pass


def pokemon_stat_menu(pokemon: PokemonWithStats):
    while True:
        response = wait_for_click("Edit:", {
            f"ATT {pokemon.stats_changes.attack} ({get_stat(pokemon, ATTACK)})": lambda: edit_stat(ATTACK, pokemon),
            f"DEF {pokemon.stats_changes.defense} ({get_stat(pokemon, DEFENSE)})": lambda: edit_stat(DEFENSE, pokemon),
            f"SP_ATT {pokemon.stats_changes.special_attack} ({get_stat(pokemon, SP_ATTACK)})": lambda: edit_stat(
                SP_ATTACK,
                pokemon),
            f"SP_DEF {pokemon.stats_changes.special_defense} ({get_stat(pokemon, SP_DEFENSE)})": lambda: edit_stat(
                SP_DEFENSE, pokemon),
            f"SPEED {pokemon.stats_changes.speed} ({get_stat(pokemon, SPEED)})": lambda: edit_stat(SPEED, pokemon),
            f"CRIT {pokemon.stats_changes.critical}": lambda: edit_stat("crit", pokemon),
            f"ACC {pokemon.stats_changes.accuracy}": lambda: edit_stat("acc", pokemon),
            f"EVS {pokemon.stats_changes.evasiveness}": lambda: edit_stat("evs", pokemon),
            f"HP {pokemon.stats_changes.hp} ({get_hp(pokemon)}/{get_max_hp(pokemon)})": lambda: edit_stat("hp", pokemon)
        })
        if response is None:
            return
        response()


def pokemon_status_menu(pokemon: PokemonWithStats):
    while True:
        value = wait_for_click("Stats (type to toggle): ", {
            f"Flinched ({pokemon.flinched})": "flinched",
            f"Paralyzed ({pokemon.paralysed})": "paralysed",
            f"Asleep ({pokemon.asleep})": "asleep",
            f"Frozen ({pokemon.frozen})": "frozen",
            f"Burned ({pokemon.burned})": "burned",
            f"Poisoned ({pokemon.poisoned})": "poisoned",
            f"Confused ({pokemon.confused})": "confused",
            f"Attracted ({pokemon.attracted})": "attracted",
            f"Trapped ({pokemon.trapped})": "trapped",

        })

        if value is None:
            return
        setattr(pokemon, value, not getattr(pokemon, value))


def pokemon_menu(pkmn: PokemonWithStats):
    return ConsoleMenu(f"{pkmn.name}", {
        "Print Details": lambda: print(get_pokemon_stats_formatted(pkmn)),
        "Change stats": lambda: pokemon_stat_menu(pkmn),
        "Change status": lambda: pokemon_status_menu(pkmn),

    })


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
