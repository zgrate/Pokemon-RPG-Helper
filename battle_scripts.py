from time import sleep
from traceback import print_tb

from ConsoleMenu import ConsoleMenu
from calculations import *
from classes import *
from data_access import get_pokemon_info, get_pokemon, POKEMON_SLEEP_WHITELIST


def get_hp_formatted(pokemon: PokemonWithStats):
    return f"{get_stat(pokemon, HP)}/{get_stat(pokemon, HP, True)} HP"


def get_pokemon_stats_formatted(pokemon: PokemonWithStats) -> str:
    text = f"\nPOKEMON STATS:\n{pokemon.name} ({pokemon.pokemon.pokemon.capitalize().replace('-', ' ')})\nAbility: {pokemon.pokemon.ability.name.capitalize()} - {pokemon.pokemon.ability.description} ({pokemon.pokemon.ability.effect})\nTypes: {', '.join(list(map(lambda d: d.name.capitalize(), pokemon.pokemon.types)))}\n"
    text += f"LVL {pokemon.level}    XP: {pokemon.xp}/{get_xp_for_level(pokemon.level + 1)}\n"
    text += f"{get_hp_formatted(pokemon)}\n"
    if pokemon.burned:
        text += "Burned!\n"
    if pokemon.flinched:
        text += "Flinched!\n"
    text += f"---------------------------\n"
    for e in pokemon.pokemon.moves:
        text += "\n"
        text += f"{e.name.capitalize()} ({e.pp - pokemon.move_pp[e.name]}/{e.pp}) - {e.flavor} ({', '.join(e.effect_text)})\n"
        text += "\n"
    text += f"---------------------------\n"
    text += f"ATT: {get_stat(pokemon, ATTACK)}({pokemon.stats_changes.attack}) DEF: {get_stat(pokemon, DEFENSE)}({pokemon.stats_changes.defense})\n" \
            f"SP_ATT: {get_stat(pokemon, SP_ATTACK)}({pokemon.stats_changes.special_attack}) SP_DEF: {get_stat(pokemon, SP_DEFENSE)}({pokemon.stats_changes.special_defense})\nSPEED: {get_stat(pokemon, SPEED)} CRIT: {pokemon.stats_changes.critical}\n"
    text += f"ACC: {pokemon.stats_changes.accuracy} EV: {pokemon.stats_changes.evasiveness}\n"
    return text


def get_team(team: list[PokemonWithStats]):
    text = "Current Team:\n"
    for pkmn in team:
        text += f"{pkmn.name.capitalize()} ({get_stat(pkmn, HP)}/{get_stat(pkmn, HP, True)} HP)\n"

    return text


def generate_random_computer_pokemon(level, pokemon_name="", pokemon_nickname=""):
    if pokemon_name == "":
        try:
            while True:
                pokemon_name = input("What pokemon would you like to encounter?")
                pkmn_info = get_pokemon_info(pokemon_name)
                if pkmn_info is None:
                    print("Pokemon not found!")
                else:
                    break
        except KeyboardInterrupt:
            return None
    else:
        pkmn_info = get_pokemon_info(pokemon_name)
        if pkmn_info is None:
            return None
    pokemon_nickname = pokemon_name if pokemon_nickname == "" else pokemon_nickname
    ability = random.choice(pkmn_info["abilities"])["ability"]["name"]
    moves = list(map(lambda d: d["move"]["name"], random.sample(pkmn_info["moves"], 4)))
    types = list(map(lambda d: d["type"]["name"], pkmn_info["types"]))
    return PokemonWithStats(pokemon_nickname, level, get_pokemon(pokemon_name, ability, types, moves),
                            computer_controlled=True)


def wait_for_click(title, items):
    print("\n")
    print(title)
    i = 1
    for key in items:
        print(str(i) + ") " + str(key))
        i += 1
    print("{}) {}".format(str(i), "exit"))

    while True:
        try:
            argument = int(input("run: "))
        except (TypeError, ValueError):
            print("Error: Invalid input type")
            continue
        except KeyboardInterrupt:
            return None

        if argument not in range(1, len(items) + 2):
            print("Error: No such item in menu")
            continue

        if argument == len(items) + 1:
            return None

        return list(items.values())[argument - 1]


def select_move_switch_run(pokemon: PokemonWithStats):
    a = {}
    for move in pokemon.pokemon.moves:
        a[f"{move.name.capitalize()} ({move.pp - pokemon.move_pp[move.name]}/{move.pp})"] = move
    a["Switch Pokemon"] = 'switch'
    a["Run"] = 'run'
    a["Others"] = "other"
    move = wait_for_click("Select your attack: ", a)
    if move is None:
        return None
    else:
        return move


def encounter(team, current_battle):
    while True:
        if current_battle["second_pokemon"] is None:
            encounter = generate_random_computer_pokemon(avarage_level(team))
            if encounter is None or encounter == "":
                print("Cancel encounter creation...")
                return
            current_battle["second_pokemon"] = encounter
            print("A wild pokemon appeared!\n")
            print(get_pokemon_stats_formatted(current_battle["second_pokemon"]))
            a = {}
            for pkmn in team:
                a[pkmn.name] = pkmn
            pokemon = wait_for_click("Who will fight?", a)
            if pokemon is None:
                return
            else:
                current_battle["first_pokemon"] = pokemon
        elif current_battle["first_pokemon"] is None:
            a = {}
            for pkmn in team:
                a[pkmn.name] = pkmn
            pokemon = wait_for_click("Who will fight?", a)
            if pokemon is None:
                return
            else:
                current_battle["first_pokemon"] = pokemon
        else:
            print(f"TURN {current_battle['turn']}")

            a = wait_for_click("What to do?", {
                "Fight": 1,
                "Change stats": 2,
            })
            if a == 2:
                met = wait_for_click("A", {
                    f"{current_battle['first_pokemon'].name} modify": "first",
                    f"{current_battle['second_pokemon'].name} modify": "second",
                    "Back": "back"
                })
                if met == "back":
                    continue
                elif met == "first":
                    pokemon_menu(current_battle["first_pokemon"]).execute()
                elif met == "second":
                    pokemon_menu(current_battle["second_pokemon"]).execute()

            result = battle_round(current_battle["first_pokemon"], current_battle["second_pokemon"],
                                  recently_first_switched=current_battle["first_switched"],
                                  recently_second_switched=current_battle["second_switched"])

            if result["status"] == "continue":
                if current_battle["first_pokemon"].burned:
                    print(f"{current_battle['first_pokemon'].name} is burned!")
                    damage_pokemon(current_battle['first_pokemon'], get_max_hp(current_battle['first_pokemon']) / 8)
                elif current_battle['first_pokemon'].poisoned:
                    print(f"{current_battle['first_pokemon'].name} is poisoned!")
                    damage_pokemon(current_battle['first_pokemon'], get_max_hp(current_battle['first_pokemon']) / 16)
                if fainted(current_battle['first_pokemon']):
                    print(f"{current_battle['first_pokemon'].name} fainted!")
                    current_battle['first_pokemon'] = None

                if current_battle["second_pokemon"].burned:
                    print(f"{current_battle['second_pokemon'].name} is burned!")
                    damage_pokemon(current_battle['second_pokemon'], get_max_hp(current_battle['second_pokemon']) / 8)
                elif current_battle['second_pokemon'].poisoned:
                    print(f"{current_battle['second_pokemon'].name} is poisoned!")
                    damage_pokemon(current_battle['second_pokemon'], get_max_hp(current_battle['second_pokemon']) / 16)
                if fainted(current_battle['second_pokemon']):
                    print(f"{current_battle['second_pokemon'].name} fainted!")
                    print(f"Team wins!")
                    return

                response = wait_for_click("What to do?", {
                    "Continue": "con",
                    f"{current_battle['first_pokemon'].name} modify": pokemon_menu(current_battle["first_pokemon"]),
                    f"{current_battle['second_pokemon'].name} modify": pokemon_menu(current_battle["second_pokemon"]),
                    "Menu": "menu"
                })
                if response is None or response == "menu":
                    return
            elif result["status"] == 'switch':
                print(f"{result['pokemon'].name} retreats!")
                if result["pokemon"] == current_battle["first_pokemon"]:
                    current_battle["first_switched"] = True
                    current_battle['first_pokemon'] = None
                else:
                    print("Emm..... second pokemon tries to switch? E?")
            elif result["status"] == "fainted":
                print(f"{result['pokemon'].name} fainted!")
                if result["pokemon"] == current_battle["first_pokemon"]:
                    current_battle['first_pokemon'] = None
                else:
                    # END OF THE BATTLE!
                    print(f"Team wins!")
                    current_battle['second_pokemon'] = None
                    return


def efectiveness_text(value):
    if value > 1:
        return "Super effective!\n"
    elif value == 0:
        return "No effect!\n"
    elif value < 1:
        return "Not very effective!\n"
    return ""


def add_stage(target: PokemonWithStats, stats):
    text = ""
    for stat in stats:
        m = stat["name"]
        c = stat["change"]
        if m == "attack":
            target.stats_changes.attack += c
            if c > 0:
                text += f"{target.name} attack rose by {c}"
            else:
                text += f"{target.name} attack fall by {c}"
        elif m == "defense":
            target.stats_changes.defense += c
            if c > 0:
                text += f"{target.name} defense rose by {c}"
            else:
                text += f"{target.name} defense fall by {c}"
        elif m == "special-attack":
            target.stats_changes.special_attack += c
            if c > 0:
                text += f"{target.name} special_attack rose by {c}"
            else:
                text += f"{target.name} special_attack fall by {c}"
        elif m == "special-defense":
            target.stats_changes.special_defense += c
            if c > 0:
                text += f"{target.name} special_defense rose by {c}"
            else:
                text += f"{target.name} special_defense fall by {c}"
        elif m == "speed":
            target.stats_changes.speed += c
            if c > 0:
                text += f"{target.name} speed rose by {c}"
            else:
                text += f"{target.name} speed fall by {c}"
        elif m == "accuracy":
            target.stats_changes.accuracy += c
            if c > 0:
                text += f"{target.name} accuracy rose by {c}"
            else:
                text += f"{target.name} accuracy fall by {c}"
        elif m == "evasion":
            target.stats_changes.evasiveness += c
            if c > 0:
                text += f"{target.name} evasiveness rose by {c}"
            else:
                text += f"{target.name} evasiveness fall by {c}"

        else:
            print("UNKNOWN STAT" + str(m))
    return text


def fight(attacker: PokemonWithStats, defender: PokemonWithStats, move: PokemonMove, DEBUG=True) -> dict:
    text = f"ATTACK:\n{attacker.name} uses {move.name.capitalize()} on {defender.name}\n"
    try:
        if not DEBUG:
            if attacker.move_pp[move.name] == move.pp:
                text += "NO PP LEFT!"
                print(text)
                return {"status": "no_pp"}
            attacker.move_pp[move.name] += 1
        if attacker.flinched:
            attacker.flinched = False
            text += "Attacker is flinched!"
            print(text)
            return {"status": "flinched"}
        if attacker.effect_round > 0:
            attacker.effect_round -= 1
            if attacker.effect_round == 0:
                if attacker.paralysed:
                    attacker.paralysed = False
                    text += f"{attacker.name} un-paralised!"
                if attacker.asleep:
                    attacker.asleep = False
                    text += f"{attacker.name} woke up!"
                if attacker.frozen:
                    attacker.frozen = False
                    text += f"{attacker.name} un-froze!"
                if attacker.burned:
                    attacker.burned = False
                    text += f"{attacker.name} extinguish!"
                if attacker.poisoned:
                    attacker.poisoned = False
                    text += f"{attacker.name} healed!"
                if attacker.confused:
                    attacker.confused = False
                    text += f"{attacker.name} un-confused!"
                if attacker.attracted:
                    attacker.attracted = False
                    text += f"{attacker.name} its not longer attracted!"
                if attacker.trapped:
                    attacker.trapped = False
                    text += f"{attacker.name} its not longer trapped!"
                text += "\n"
            else:
                if attacker.paralysed:
                    if percentage_hit_chance(33):
                        text += f"{attacker.name} is still paralyzed!"
                        return {"status": "paralyzed_failed"}
                if attacker.asleep and not any(x for x in POKEMON_SLEEP_WHITELIST if x == move.name):
                    text += f"{attacker.name} is asleep!"
                    return {"status": "asleep"}
                if attacker.frozen:
                    text += f"{attacker.name} is frozen!"
                    return {"status": "frozen"}

                if attacker.confused:
                    if percentage_hit_chance(33):
                        text += f"{attacker.name} hit yourself in confusion!\n"
                        damage = damage_confusion(attacker)
                        text += f"Dealt {damage} HP!\n"
                        damage_pokemon(attacker, damage)
                        return {"status": "confusion_hit"}

                if attacker.attracted:
                    if percentage_hit_chance(50):
                        text += f"{attacker.name} is in love!"
                        return {"status": "love"}

        hit = percentage_hit_chance(calculate_accuracy(move.accuracy, attacker.stats_changes.accuracy,
                                                       defender.stats_changes.evasiveness))
        if not hit:
            text += "But if failed!"
            print(text)
            return {"status": "failed"}

        if move.damage_class == "status":
            if len(move.stat_changes) > 0:
                if move.target == "user":
                    text += add_stage(attacker, move.stat_changes)
                    print(text)
                    return {"status": "status_attack_self"}
                else:
                    text += add_stage(defender, move.stat_changes)
                    print(text)
                    return {"status": "status_attack_other"}

        if move.power is None:
            move.power = random.randint(0, 100)
        damage = calculate_damage(attacker, defender, move, attacker.stats_changes.critical,
                                  attacker.burned)  # TODO: Hmm... crits from abilities

        text += efectiveness_text(damage["type_effectiveness"])

        if damage["critical"]:
            text += "Critical hit!\n"

        text += f"Dealt {damage['damage']} HP!\n"
        damage_pokemon(defender, damage["damage"])
        text += f"{defender.name} {get_stat(defender, HP)}/{get_stat(defender, HP, True)} HP"
        if move.flinch_chance > 0 and random.randint(0, 101) < move.flinch_chance:
            defender.flinched = True
            text += f"{defender.name} flinched!\n"

        if not has_non_violate_status(pokemon=defender):
            if move.ailment == STATUSES["STATUS_PARALYSIS"]:
                if percentage_hit_chance(move.effect_chance):
                    defender.paralysed = True
                    defender.effect_round = random.randint(2, 5)
                    text += f"{defender.name} is paralysed!\n"
            elif move.ailment == STATUSES["STATUS_SLEEP"]:
                if percentage_hit_chance(move.effect_chance):
                    defender.asleep = True
                    defender.effect_round = random.randint(3, 7)
                text += f"{defender.name} is asleep"
            elif move.ailment == STATUSES["STATUS_FREEZE"]:
                if percentage_hit_chance(move.effect_chance):
                    defender.frozen = True
                    defender.effect_round = random.randint(3, 7)
                text += f"{defender.name} is frozen"
            elif move.ailment == STATUSES["STATUS_BURN"]:
                if percentage_hit_chance(move.effect_chance):
                    defender.burned = True
                    defender.effect_round = random.randint(3, 7)
                    text += f"{defender.name} burned!\n"
            elif move.ailment == STATUSES["STATUS_POISON"]:
                if percentage_hit_chance(move.effect_chance):
                    defender.poisoned = True
                    defender.effect_round = random.randint(3, 7)
                    text += f"{defender.name} is poisoned!"
        elif move.ailment == STATUSES["STATUS_CONFUSION"]:
            if percentage_hit_chance(move.effect_chance):
                defender.confused = True
                defender.effect_round = random.randint(2, 5)
                text += f"{defender.name} is confused!"
        elif move.ailment == STATUSES["STATUS_INFATUATION"]:
            if percentage_hit_chance(move.effect_chance):
                defender.attracted = True
                defender.effect_round = random.randint(2, 5)
                text += f"{defender.name} is attracted!"
        elif move.ailment == STATUSES["STATUS_TRAP"]:
            if percentage_hit_chance(move.effect_chance):
                # defender.trapped = True
                text += f"{defender.name} is confused!"
        elif move.ailment == STATUSES["STATUS_NIGHTMARE"]:
            if percentage_hit_chance(move.effect_chance):
                # TODO
                text += f"!!{defender.name} has a nightmare!!"
        elif move.ailment == STATUSES["STATUS_TORMENT"]:
            if percentage_hit_chance(move.effect_chance):
                # TODO
                text += f"{defender.name} is tormented!"
        elif move.ailment == STATUSES["STATUS_DISABLE"]:
            if percentage_hit_chance(move.effect_chance):
                # TODO
                text += f"{defender.name} has attack disabled!"
        elif move.ailment == STATUSES["STATUS_YAWN"]:
            if percentage_hit_chance(move.effect_chance):
                # TODO
                text += f"{defender.name} is drowzy..."
        elif move.ailment == STATUSES["STATUS_HEAL_BLOCK"]:
            if percentage_hit_chance(move.effect_chance):
                # TODO
                text += f"{defender.name} cant heal!"
        elif move.ailment == STATUSES["STATUS_NO_TYPE_IMMUNITY"]:
            if percentage_hit_chance(move.effect_chance):
                # TODO
                text += f"{defender.name} is not immune!!"
        elif move.ailment == STATUSES["STATUS_LEECH_SEED"]:
            if percentage_hit_chance(move.effect_chance):
                # TODO
                text += f"{defender.name} is leached!"
        elif move.ailment == STATUSES["STATUS_EMBARGO"]:
            if percentage_hit_chance(move.effect_chance):
                # defender.poisoned = True
                text += f"{defender.name} is embargoed!"
        elif move.ailment == STATUSES["STATUS_PERISH_SONG"]:
            if percentage_hit_chance(move.effect_chance):
                # defender.poisoned = True
                text += f"{defender.name} is perished!"
        elif move.ailment == STATUSES["STATUS_INGRAIN"]:
            if percentage_hit_chance(move.effect_chance):
                # defender.poisoned = True
                text += f"{defender.name} is ingrained!"
        elif move.ailment == STATUSES["STATUS_SILENCE"]:
            if percentage_hit_chance(move.effect_chance):
                # defender.poisoned = True
                text += f"{defender.name} is silenced!"
        elif move.ailment == STATUSES["STATUS_TAR_SHOT"]:
            if percentage_hit_chance(move.effect_chance):
                # defender.poisoned = True
                text += f"{defender.name} is tar shot!"

        print(text)
        return {"status": "ok"}
    except Exception as e:
        print(f"So far generated:\n{text}")
        print()
        print(str(e))
        print()
        sleep(0.1)
        print_tb(e.__traceback__)
        return {"status": "error"}


def pokemon_get_move_switch_run(pokemon: PokemonWithStats):
    while True:
        if pokemon.computer_controlled:
            return random.choice(pokemon.pokemon.moves)
        else:
            response = select_move_switch_run(pokemon)
            if response is None:
                return None
            return response


def damage_pokemon(pokemon: PokemonWithStats, damage):
    pokemon.stats_changes.hp += math.floor(damage)
    if get_stat(pokemon, HP) < 0:
        pokemon.stats_changes.hp = get_stat(pokemon, HP, True)


def heal_pokemon(pokemon: PokemonWithStats, healing):
    pokemon.stats_changes.hp -= math.floor(healing)
    if pokemon.stats_changes.hp < 0:
        pokemon.stats_changes.hp = 0


def get_hp(pokemon: PokemonWithStats):
    return get_stat(pokemon, HP)


def get_max_hp(pokemon: PokemonWithStats):
    return get_stat(pokemon, HP, True)


def battle_round(first_pokemon: PokemonWithStats, second_pokemon: PokemonWithStats, recently_first_switched=False,
                 recently_second_switched=False, can_switch_first=True, can_switch_second=True, can_run_first=True,
                 can_run_second=True):
    first_pokemon_move: PokemonMove
    second_pokemon_move: PokemonMove

    print(
        f"{first_pokemon.name} {get_stat(first_pokemon, HP)}/{get_stat(first_pokemon, HP, True)} vs {second_pokemon.name} {get_stat(second_pokemon, HP)}/{get_stat(second_pokemon, HP, True)}\n")

    first_pokemon_move_response = pokemon_get_move_switch_run(first_pokemon)
    if first_pokemon_move_response is None:
        return {"status": "error_move_choice", "pokemon": first_pokemon}
    elif first_pokemon_move_response == "switch":
        return {"status": "switch", "pokemon": first_pokemon}
    elif first_pokemon_move_response == "run":
        return {"status": "run", "pokemon": first_pokemon}
    else:
        first_pokemon_move = first_pokemon_move_response

    second_pokemon_move_response = pokemon_get_move_switch_run(second_pokemon)
    if second_pokemon_move_response is None:
        return {"status": "error_move_choice", "pokemon": second_pokemon}
    elif second_pokemon_move_response == "switch":
        return {"status": "switch", "pokemon": second_pokemon}
    elif second_pokemon_move_response == "run":
        return {"status": "run", "pokemon": second_pokemon}
    else:
        second_pokemon_move = second_pokemon_move_response

    first_attack = first_pokemon
    first_move = first_pokemon_move
    second_attack = second_pokemon
    second_move = second_pokemon_move

    if first_pokemon_move.priority < second_pokemon_move.priority or get_stat(first_pokemon, SPEED) < get_stat(
            second_pokemon, SPEED):
        first_attack = second_pokemon
        first_move = second_pokemon_move
        second_attack = first_pokemon
        second_move = first_pokemon_move

    print("-------------------")
    fight(first_attack, second_attack, first_move)  # CHECK_FAINT

    if fainted(second_attack):
        print(f"{second_attack.name} fainted!")
        return {"status": "fainted", "pokemon": second_attack}

    print("-------------------")
    sleep(1)
    fight(second_attack, first_attack, second_move)
    if fainted(first_attack):
        print(f"{first_attack.name} fainted!")
        return {"status": "fainted", "pokemon": first_attack}
    print("--------------------")

    return {"status": "continue"}


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

            if fainted(pokemon):
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
