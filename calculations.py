import math
import random

import classes
from classes import PokemonWithStats, PokemonMove, ATTACK, DEFENSE, SP_ATTACK, SP_DEFENSE, HP
from data_access import get_type_object


def get_stat(pokemon_with_stats, stat_name, ignore_differences=False):
    match stat_name:
        case classes.ATTACK:
            return calculate_other_stat(pokemon_with_stats.pokemon.base_stats.attack, pokemon_with_stats.level,
                                        stage=(
                                            pokemon_with_stats.stats_changes.attack if not ignore_differences else 0))
        case classes.DEFENSE:
            return calculate_other_stat(pokemon_with_stats.pokemon.base_stats.defense, pokemon_with_stats.level,
                                        stage=(
                                            pokemon_with_stats.stats_changes.defense if not ignore_differences else 0))
        case classes.SP_ATTACK:
            return calculate_other_stat(pokemon_with_stats.pokemon.base_stats.special_attack, pokemon_with_stats.level,
                                        stage=(
                                            pokemon_with_stats.stats_changes.special_attack if not ignore_differences else 0))
        case classes.SP_DEFENSE:
            return calculate_other_stat(pokemon_with_stats.pokemon.base_stats.special_defense, pokemon_with_stats.level,
                                        stage=(
                                            pokemon_with_stats.stats_changes.special_defense if not ignore_differences else 0))
        case classes.SPEED:
            return calculate_other_stat(pokemon_with_stats.pokemon.base_stats.speed, pokemon_with_stats.level,
                                        stage=pokemon_with_stats.stats_changes.speed)
        case classes.HP:
            return calculate_hp(pokemon_with_stats.pokemon.base_stats.hp, pokemon_with_stats.level) - (
                pokemon_with_stats.stats_changes.hp if not ignore_differences else 0)


def random_chance(one_over_: int, compare_against=1):
    return random.randint(0, one_over_) == compare_against


def crit(stage: int):
    if stage == 0:
        return random_chance(16)
    elif stage == 1:
        return random_chance(8)
    elif stage == 2:
        return random_chance(2)
    elif stage > 3:
        return True
    else:
        return False


def calculate_type_effectiveness(defender: PokemonWithStats, move: PokemonMove):
    move_type = get_type_object(move.attack_type)
    typ = defender.pokemon.types[0].name
    if typ in move_type.super_effective:
        multi = 2
    elif typ in move_type.not_very_effective:
        multi = 0.5
    elif typ in move_type.no_effective:
        multi = 0
    else:
        multi = 1
    if len(defender.pokemon.types) == 2:
        typ2 = defender.pokemon.types[1]
        if typ2 in move_type.super_effective:
            multi *= 2
        elif typ2 in move_type.not_very_effective:
            multi *= 0.5
        elif typ2 in move_type.no_effective:
            multi *= 0
        else:
            multi *= 1
    return multi


def calculate_base_damage(attacker: PokemonWithStats, defender: PokemonWithStats, move: PokemonMove):
    a_div_d = float(get_stat(attacker, ATTACK)) / float(get_stat(defender,
                                                                 DEFENSE)) if move.damage_class == "physical" else float(
        get_stat(attacker, SP_ATTACK)) / float(
        get_stat(defender, SP_DEFENSE))
    return (((float(attacker.level * 2.0) / 5.0) * move.power * a_div_d) / 50.0) + 2.0


def calculate_damage(attacker: PokemonWithStats, defender: PokemonWithStats, move: PokemonMove,
                     critical_attack_stage: int, burned: bool, other=1.0):
    targets = 1.0
    weather = 1.0
    badge = 1.0
    critical_multi = 2.0 if crit(critical_attack_stage) else 1.0
    randomised = float(random.randint(85, 101)) / 100
    stab = 1.5 if any(x for x in attacker.pokemon.types if x.name == move.attack_type) else 1.0
    type_eff = calculate_type_effectiveness(defender, move)

    damage = calculate_base_damage(attacker, defender,
                                   move) * targets * weather * badge * critical_multi * randomised * stab * type_eff \
             * (0.5 if burned and move.damage_class == "physical" else 1.0) * float(other)

    return {
        "damage": math.floor(damage),
        "critical": critical_multi > 1,
        "type_effectiveness": type_eff
    }


def calculate_hp(base_stat, level, iv=0, ev=0):
    return math.floor((((2 * base_stat) + iv + math.floor(ev / 4)) * level) / 100.0) + level + 10


def get_stage_modifier_stat(stage):
    if stage == 0:
        return 1
    elif stage > 0:
        return (2 + stage) / 2
    else:
        return 2 / (2 + abs(stage))


def calculate_other_stat(base_stat, level, nature_modifier=1, stage=0, iv=0, ev=0):
    return math.floor((math.floor(
        ((2 * base_stat) + iv + math.floor(ev / 4)) * level) + 5) * nature_modifier * get_stage_modifier_stat(stage))


def stage_accuracy(stage_accuracy):
    if stage_accuracy == 0:
        return 1
    elif stage_accuracy > 0:
        return (stage_accuracy + 3) / 3
    else:
        return 3 / (abs(stage_accuracy) + 3)


def stage_evasion(stage_evasion):
    if stage_evasion == 0:
        return 1
    elif stage_evasion < 0:
        return 3 / (abs(stage_evasion) + 3)
    else:
        return (stage_evasion + 3) / 3


def calculate_accuracy(move_accuracy, acc_stage, eva_stage, other=1):
    if move_accuracy is not None:
        return move_accuracy * stage_accuracy(acc_stage - eva_stage) * other
    return 100


def percentage_hit_chance(accuracy):
    # print(accuracy)
    return random.randint(0, 100) <= accuracy


def get_xp_for_level(target_level):
    return (target_level ** 3)


def fainted(pokemon: PokemonWithStats):
    return get_stat(pokemon, HP) <= 0


def avarage_level(team: list[PokemonWithStats]):
    return sum(x.level for x in team) / len(team)


def has_non_violate_status(pokemon: PokemonWithStats):
    return pokemon.burned or pokemon.frozen or pokemon.paralysed or pokemon.poisoned or pokemon.asleep


CONFUSION_MOVE = PokemonMove("Confusion", 100, 40, 100, 0, "physical", "normal", "", "", 0, 0, 0, 0, 0, [], "", {}, 0)


def damage_confusion(pokemon: PokemonWithStats):
    return calculate_base_damage(pokemon, pokemon, CONFUSION_MOVE) * float(random.randint(85, 101)) / 100
