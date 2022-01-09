import json
import os
import random

import generator2
from calculations import percentage_hit_chance
from data_access import get_items, get_team_skills

items = get_items()
skills = get_team_skills()


def random_pokemons_with_type(allowed_types):
    all_allowed_pokemon = []
    for type_name in allowed_types:
        if not os.path.exists(os.path.join("types", type_name + ".json")):
            return None
        with open(os.path.join("types", type_name + ".json"), "rb") as typ:
            typeJson = json.loads(typ.read().decode("utf-8"))
            all_allowed_pokemon += list(map(lambda d: d["pokemon"]["name"], typeJson["pokemon"]))
    return random.sample(all_allowed_pokemon, random.randint(0, 2))


def generate_floor(types, filename="map.png"):
    rooms = generator2.generate_draw_map(filename)
    dungeon_floor = []
    for i in range(len(rooms)):
        a = {
            'id': i,
            'room': rooms[i],
            'items': list(map(lambda d: d.copy(), random.sample(items, random.randint(0, 3)))),
            'exit': False,
            'pokemons': random_pokemons_with_type(types),
        }

        if percentage_hit_chance(60):
            a["items"].append({"name": "Gold", "description": f"Gold coins. {random.randint(0, 200)} to be precise"})
        dungeon_floor.append(a)

    random.choice(dungeon_floor)["exit"] = True
    return dungeon_floor


def room_details(room_dict: dict):
    text = f"Room number {room_dict['id']}\nItems in room:\n"
    for e in room_dict["items"]:
        text += f"- {e['name']} - {e['description']}\n"
    text += "\nPokemons on floor:\n"
    for pkmn in room_dict["pokemons"]:
        text += f"- {pkmn.capitalize()}\n"
    if room_dict["exit"]:
        text += f"THERE IS EXIT ON THIS FLOOR!"
    return text


def navigate_floor(dungeon_floor: dict):
    try:
        while True:
            room_number = int(input(f"Select room number for details ({len(dungeon_floor)}) "))
            if room_number >= len(dungeon_floor):
                print("Invalid number")
            else:
                print(room_details(next(room for room in dungeon_floor if room["id"] == room_number)))
    except BaseException:
        return "back"
