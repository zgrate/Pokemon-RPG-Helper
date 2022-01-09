import json
import os
from typing import Optional

import requests

from classes import Stats, PokemonType, PokemonMove, PokemonAbility, Pokemon

POKEMON_MOVE_BLACKLIST = ["flinch", "snatch"]

POKEMON_SLEEP_WHITELIST = ["sleep-talk"]


def data_folder(file_name, extension="json"):
    return os.path.join("data", file_name + f".{extension}")


def cache_pokemon_folder(file_name):
    return os.path.join("cache/pokemon", file_name + ".json")


def cache_moves_folder(file_name):
    return os.path.join("cache/moves", file_name + ".json")


def cache_abilities_folder(file_name):
    return os.path.join("cache/abilities", file_name + ".json")


def search_en_lang_entry(list_to_scan):
    return next(x for x in list_to_scan if x["language"]["name"] == "en")


def get_pokemon_info(pokemon_name: str):
    pokemon_name = pokemon_name.lower().replace(" ", "_")
    if not os.path.exists(cache_pokemon_folder(pokemon_name)):
        with open(data_folder("pokemon"), "r") as pokemons:
            allPokemons = json.load(pokemons)
            found_pokemon = next(
                (found_pokemon for found_pokemon in allPokemons["results"] if found_pokemon["name"] == pokemon_name),
                None)
            if found_pokemon is None:
                return None
            else:
                fetched = requests.get(found_pokemon["url"])
                if fetched.ok:
                    with open(cache_pokemon_folder(pokemon_name), "wb") as pokemon:
                        pokemon.write(fetched.text.encode("utf-8"))
                    return fetched.json()
                else:
                    return None
    else:
        with open(cache_pokemon_folder(pokemon_name)) as pkmn:
            return json.load(pkmn)


def get_base_stats(pokemon_name: str) -> Optional[Stats]:
    a = get_pokemon_info(pokemon_name)
    if a is not None:
        stats = a["stats"]

        def s(value):
            return next((statistic["base_stat"] for statistic in stats if statistic["stat"]["name"] == value), None)

        return Stats(s("hp"), s("attack"), s("defense"), s("special-attack"), s("special-defense"), s("speed"))
    return None


def get_pokemon_species(pokemon_name: str):
    pokemon_name = pokemon_name.lower().replace(" ", "_")
    pkmn = get_pokemon_info(pokemon_name)
    if pkmn is None:
        return None
    if not os.path.exists(cache_pokemon_folder(pokemon_name + "_species")):
        fetched = requests.get(pkmn["species"]["url"])
        if fetched.ok:
            with open(cache_pokemon_folder(pokemon_name + "_species"), "wb") as pokemon:
                pokemon.write(fetched.text.encode("utf-8"))
            return fetched.json()
        else:
            return None
    else:
        with open(cache_pokemon_folder(pokemon_name + "_species"), "rb") as pkmn:
            return json.loads(pkmn.read().decode("utf-8"))


def get_pokemon_description(pokemon_name: str) -> Optional[str]:
    pkmn = get_pokemon_species(pokemon_name)
    if pkmn is None:
        return None
    return search_en_lang_entry(pkmn["flavor_text_entries"])["flavor_text"]


def get_move_data(move_name: str) -> Optional[PokemonMove]:
    move = move_name.lower().replace(" ", "-")
    if not os.path.exists(cache_moves_folder(move)):
        fetched = requests.get("https://pokeapi.co/api/v2/move/" + move)
        if fetched.ok:
            with open(cache_moves_folder(move), "wb") as moveFile:
                moveFile.write(fetched.text.encode("utf-8"))
            jsoned = fetched.json()
        else:
            return None
    else:
        with open(cache_moves_folder(move), "rb") as moveFile:
            jsoned = json.loads(moveFile.read().decode("utf-8"))

    return PokemonMove(move_name, jsoned["accuracy"], jsoned["power"], jsoned["pp"], jsoned["priority"],
                       jsoned["damage_class"]["name"], jsoned["type"]["name"],
                       search_en_lang_entry(jsoned["flavor_text_entries"])["flavor_text"],
                       list(map(lambda d: d["effect"], jsoned["effect_entries"])),
                       jsoned["meta"]["flinch_chance"], jsoned["meta"]["healing"], jsoned["meta"]["drain"],
                       jsoned["meta"]["min_turns"], jsoned["meta"]["max_turns"],
                       list(map(lambda d: {"name": d["stat"]["name"], 'change': d["change"]}, jsoned["stat_changes"])),
                       jsoned["target"]["name"], jsoned["meta"]["ailment"]["name"], jsoned["effect_chance"])


def get_type_object(type_name: str) -> Optional[PokemonType]:
    if not os.path.exists(os.path.join("types", type_name + ".json")):
        return None
    with open(os.path.join("types", type_name + ".json"), "rb") as typ:
        typeJson = json.loads(typ.read().decode("utf-8"))

        def find(damage_type):
            return list(map(lambda d: d["name"], typeJson["damage_relations"][damage_type]))

        return PokemonType(type_name, find('double_damage_to'), find('half_damage_to'), find('no_damage_to'))


def get_ability_data(ability_name: str) -> Optional[PokemonAbility]:
    ability = ability_name.lower().replace(" ", "-")
    if not os.path.exists(cache_abilities_folder(ability)):
        fetched = requests.get("https://pokeapi.co/api/v2/ability/" + ability)
        if fetched.ok:
            with open(cache_abilities_folder(ability), "wb") as abilityFile:
                abilityFile.write(fetched.text.encode("utf-8"))
            jsoned = fetched.json()
        else:
            return None
    else:
        with open(cache_abilities_folder(ability), "rb") as abilityFile:
            jsoned = json.loads(abilityFile.read().decode("utf-8"))
    return PokemonAbility(ability_name, search_en_lang_entry(jsoned["flavor_text_entries"])["flavor_text"],
                          search_en_lang_entry(jsoned["effect_entries"])["effect"])


def get_pokemon(pokemon_name, ability, types, moves):
    return Pokemon(pokemon_name, get_pokemon_description(pokemon_name), get_ability_data(ability),
                   list(map(lambda t: get_type_object(t), types)),
                   list(map(lambda m: get_move_data(m), moves)), get_base_stats(pokemon_name))


def get_items(file_name="items_list"):
    with open(data_folder(file_name, "txt"), encoding="utf-8") as items_file:
        lines = items_file.readlines()

        currentCategory = ""
        items = []
        for line in lines:
            split = line.split("\t")
            if split[0] == "Category":
                currentCategory = split[1].strip()
            else:
                items.append({"category": currentCategory, "name": split[0].strip(), "description": split[1].strip(),
                              "location": (split[2].strip() if len(split) > 2 else "")})

        return items


def get_team_skills(file_name="team_skills_tab_separated"):
    with open(data_folder(file_name, "txt"), encoding="utf-8") as skills_file:
        lines = skills_file.readlines()

        def tf(line: str):
            split = line.split("\t")
            return {"name": split[0].strip(), "description": split[1].strip()}

        return list(map(tf, lines))
