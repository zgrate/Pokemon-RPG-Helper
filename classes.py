class Stats:

    def __init__(self, hp=0, attack=0, defense=0, special_attack=0, special_defense=0, speed=0, accuracy=0,
                 evasiveness=0,
                 critical=0):
        self.hp = hp
        self.attack = attack
        self.defense = defense
        self.special_attack = special_attack
        self.special_defense = special_defense
        self.speed = speed
        self.accuracy = accuracy
        self.evasiveness = evasiveness
        self.critical = critical

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)


STATUSES = {
    'STATUS_UNKNOWN': 'unknown',
    'STATUS_NONE': 'none',
    'STATUS_PARALYSIS': 'paralysis',
    'STATUS_SLEEP': 'sleep',
    'STATUS_FREEZE': 'freeze',
    'STATUS_BURN': 'burn',
    'STATUS_POISON': 'poison',
    'STATUS_CONFUSION': 'confusion',
    'STATUS_INFATUATION': 'infatuation',
    'STATUS_TRAP': 'trap',
    'STATUS_NIGHTMARE': 'nightmare',
    'STATUS_TORMENT': 'torment',
    'STATUS_DISABLE': 'disable',
    'STATUS_YAWN': 'yawn',
    'STATUS_HEAL_BLOCK': 'heal-block',
    'STATUS_NO_TYPE_IMMUNITY': 'no-type-immunity',
    'STATUS_LEECH_SEED': 'leech-seed',
    'STATUS_EMBARGO': 'embargo',
    'STATUS_PERISH_SONG': 'perish-song',
    'STATUS_INGRAIN': 'ingrain',
    'STATUS_SILENCE': 'silence',
    'STATUS_TAR_SHOT': 'tar-shot',
}


class PokemonMove:
    def __init__(self, name: str, accuracy, power, pp, priority, damage_class, attack_type, flavor, effect_text,
                 flinch_chance, healing, drain, min_turns, max_turns, stat_changes: list[dict], target, ailment: dict,
                 effect_chance):
        self.max_turns = max_turns
        self.min_turns = min_turns
        self.target = target
        self.stat_changes = stat_changes
        self.drain = drain
        self.healing = healing
        self.accuracy = accuracy
        self.power = power
        self.pp = pp
        self.priority = priority
        self.damage_class = damage_class
        self.attack_type = attack_type
        self.flavor = flavor
        self.effect_text = effect_text
        self.flinch_chance = flinch_chance
        self.ailment = ailment
        self.name = name
        self.effect_chance = effect_chance

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)


class PokemonType:
    def __init__(self, name, super_effective: list[str], not_very_effective: list[str], no_effective: list[str]):
        self.name = name
        self.super_effective = super_effective
        self.not_very_effective = not_very_effective
        self.no_effective = no_effective

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)


class PokemonAbility:
    def __init__(self, name, description, effect):
        self.name = name
        self.description = description
        self.effect = effect

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)


class Pokemon:

    def __init__(self, pokemon, description, ability: PokemonAbility, types: list[PokemonType],
                 moves: list[PokemonMove], base_stats: Stats):
        self.description = description
        self.base_stats = base_stats
        self.pokemon = pokemon
        self.ability = ability
        self.types = types
        self.moves = moves

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)


ATTACK = "attack"
SP_ATTACK = "sp_attack"
DEFENSE = "defence"
SP_DEFENSE = "sp_defence"
HP = "hp"
SPEED = "speed"


class PokemonWithStats:
    def __init__(self, name: str, level: int, pokemon: Pokemon, computer_controlled=False, xp=0):
        self.name = name
        self.pokemon = pokemon
        self.level = level
        self.xp = xp

        self.move_pp = {}

        self.notes = []
        self.stats_changes = Stats(0, 0, 0, 0, 0, 0, 0, 0, 0)
        self.computer_controlled = computer_controlled
        for e in self.pokemon.moves:
            self.move_pp[e.name] = 0

        self.flinched = False
        self.paralysed = False
        self.asleep = False
        self.frozen = False
        self.burned = False
        self.poisoned = False
        self.confused = False
        self.attracted = False
        self.trapped = False
        self.effect_round = 0

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)

    def reset_stats_changes(self):
        self.stats_changes.speed = 0
        self.stats_changes.attack = 0
        self.stats_changes.accuracy = 0
        self.stats_changes.defense = 0
        self.stats_changes.special_attack = 0
        self.stats_changes.special_defense = 0
        self.stats_changes.evasiveness = 0
        self.stats_changes.critical = 0

    def reset_status_effects(self):
        self.flinched = False
        self.paralysed = False
        self.asleep = False
        self.frozen = False
        self.burned = False
        self.poisoned = False
        self.confused = False
        self.attracted = False
        self.trapped = False

    def damage(self, dmg):
        self.stats_changes.hp += dmg
