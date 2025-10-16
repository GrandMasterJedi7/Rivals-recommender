"""Rivals helper

This script asks the player for gamemode, map and role then recommends
top 3 heroes for that role on the selected map.

Classes introduced:
- Hero: simple data holder with name, roles and per-map scores
- Recommender: contains dataset and scoring logic

To extend: add more Hero instances to the HEROES list or tweak scoring rules.
"""

from typing import List, Dict, Tuple


class Hero:
    """Representation of a hero.

    Attributes:
        name: display name
        roles: list of roles this hero can play (e.g., 'DPS', 'Support', 'Tank')
        map_scores: optional mapping from map name (lowercase) to a numeric score
    """

    def __init__(self, name: str, roles: List[str], map_scores: Dict[str, float] = None,
                 role_proficiencies: Dict[str, float] = None, map_role_bonus: Dict[Tuple[str, str], float] = None):
        """Create a hero.

        role_proficiencies: optional mapping role -> 0.0..1.0 indicating how well
        this hero performs in that role (1.0 = perfect fit).

        map_role_bonus: optional mapping (map_name.lower(), role.lower()) -> multiplier
        applied on top of other factors (e.g., 1.1 for 10% bonus).
        """
        self.name = name
        self.roles = [r.lower() for r in roles]
        # raw scores (e.g., 0-10 scale) per map
        self.map_scores = {k.lower(): v for k, v in (map_scores or {}).items()}
        # role proficiency 0-1
        self.role_proficiencies = {k.lower(): float(v) for k, v in (role_proficiencies or {}).items()}
        # map-role bonus multipliers: key is (map, role)
        self.map_role_bonus = { (m.lower(), r.lower()): float(b) for (m, r), b in (map_role_bonus or {}).items() }

    def raw_map_score(self, map_name: str) -> float:
        """Return raw numeric map score (default 0).

        Raw scale is assumed to be 0..10 by convention; normalization happens in Recommender.
        """
        return self.map_scores.get(map_name.lower(), 0.0)

    def role_proficiency(self, role: str) -> float:
        return self.role_proficiencies.get(role.lower(), 0.0)

    def map_role_bonus_multiplier(self, map_name: str, role: str) -> float:
        return self.map_role_bonus.get((map_name.lower(), role.lower()), 1.0)


class Recommender:
    """Recommend heroes based on role and map.

    Simple algorithm: filter heroes that can play the requested role, then sort
    by the per-map score (descending). Ties are broken alphabetically.
    """

    def __init__(self, heroes: List[Hero]):
        self.heroes = heroes

    def recommend(self, role: str, map_name: str, top_n: int = 3,
                  map_weight: float = 0.6, role_weight: float = 0.35, bonus_weight: float = 0.05) -> List[Tuple[Hero, float]]:
        """Recommend heroes using a composite weighted score.

        Components:
        - normalized map score (assumes raw map score is 0..10) normalized to 0..1
        - role proficiency (0..1)
        - map-role bonus multiplier (applied as an additive factor after weights)

        We compute: base = map_norm * map_weight + role_prof * role_weight
        final_score = base * bonus_multiplier ** (bonus_weight * 10)

        The bonus_weight is small; to make multipliers like 1.1 have a modest impact we use an exponent.
        Return list of (Hero, final_score) sorted descending.
        """
        role_lc = role.lower()
        candidates = [h for h in self.heroes if role_lc in h.roles]

        def compute_score(h: Hero) -> float:
            raw = h.raw_map_score(map_name)  # expect 0..10
            map_norm = max(0.0, min(1.0, raw / 10.0))
            role_prof = h.role_proficiency(role_lc)
            base = map_norm * map_weight + role_prof * role_weight
            bonus = h.map_role_bonus_multiplier(map_name, role_lc)
            # Apply bonus as a small exponential factor so 1.1 -> noticeable but not huge
            final = base * (bonus ** (bonus_weight * 10))
            return round(final, 4)

        scored = [(h, compute_score(h)) for h in candidates]
        scored.sort(key=lambda t: (-t[1], t[0].name.lower()))
        return scored[:top_n]


# Some heroes with made-up data for demonstration. Some have flex roles but the data is almost certainly innacurate.
HEROES = [
    Hero('Spider-Man', ['DPS'], {'midtown': 9.5, 'arakko': 7.0, 'central park': 9.0},
        role_proficiencies={'DPS': 0.95},
        map_role_bonus={('midtown', 'DPS'): 1.05}),
    Hero('Wolverine', ['DPS', 'Tank'], {'midtown': 8.0, 'yggdrasill path': 8.5, 'krakoa': 7.5},
        role_proficiencies={'DPS': 0.85, 'Tank': 0.9}),
    Hero('Storm', ['Support', 'DPS'], {'central park': 8.5, 'symbiotic surface': 9.0},
        role_proficiencies={'Support': 0.9, 'DPS': 0.7},
        map_role_bonus={('symbiotic surface', 'support'): 1.08}),
    Hero('Doctor Strange', ['Support'], {'central park': 7.0, 'hall of djalia': 8.5},
        role_proficiencies={'Support': 0.92}),
    Hero('Magneto', ['DPS'], {'shin-shibuya': 8.8, 'spider-islands': 7.9},
        role_proficiencies={'DPS': 0.88},
        map_role_bonus={('shin-shibuya', 'dps'): 1.12}),
    Hero('Iron Man', ['DPS', 'Support'],
        {'central park': 8.0, 'midtown': 8.8, 'royal palace': 7.2},
        role_proficiencies={'DPS': 0.9, 'Support': 0.6},
        map_role_bonus={('midtown', 'dps'): 1.04}),
    Hero('Black Panther', ['DPS', 'Support'],
        {'birnin tchalla': 9.4, 'central park': 7.8, 'krakoa': 8.2},
        role_proficiencies={'DPS': 0.9, 'Support': 0.7},
        map_role_bonus={('birnin tchalla', 'dps'): 1.08}),
    Hero('Hulk', ['Tank', 'DPS'],
        {'krakoa': 9.0, 'hells heaven': 8.6, 'yggdrasill path': 7.0},
        role_proficiencies={'Tank': 0.95, 'DPS': 0.6}),
    Hero('Scarlet Witch', ['Support', 'DPS'],
        {'hall of djalia': 9.1, 'symbiotic surface': 8.4, 'shin-shibuya': 8.0},
        role_proficiencies={'Support': 0.9, 'DPS': 0.75},
        map_role_bonus={('hall of djalia', 'support'): 1.07}),
    Hero('Groot', ['Tank', 'Support'],
        {'royal palace': 8.6, 'yggdrasill path': 8.0},
        role_proficiencies={'Tank': 0.88, 'Support': 0.7}),
    Hero('Punisher', ['DPS'],
        {'midtown': 8.9, 'spider-islands': 7.6, 'arakko': 6.5},
        role_proficiencies={'DPS': 0.86}),
    Hero('Black Widow', ['DPS', 'Support'],
        {'midtown': 8.3, 'shin-shibuya': 8.1, 'central park': 7.5},
        role_proficiencies={'DPS': 0.82, 'Support': 0.65}),
]


def _prompt_choice(prompt: str, options: List[str]) -> str:
    """Prompt the user until they provide a case-insensitive match from options."""
    opts_lc = [o.lower() for o in options]
    while True:
        print(prompt)
        resp = input('> ').strip()
        if resp.lower() in opts_lc:
            # return the canonical option (original casing)
            return options[opts_lc.index(resp.lower())]
        print("Invalid choice. Options are:\n - " + "\n - ".join(options))


def main():
    gamemodes = {
        'Convergence': ['Central Park', 'Hall of Djalia', 'Symbiotic Surface', 'Shin-Shibuya'],
        'Convoy': ['Midtown', 'Arakko', 'Spider-Islands', 'Yggdrasill Path'],
        'Domination': ['Birnin TChalla', 'Celestial Husk', "Hells Heaven", 'Krakoa', 'Royal Palace'],
    }

    print('Which gamemode are you playing?')
    gamemode = _prompt_choice('Choose a gamemode:', list(gamemodes.keys()))
    map_choice = _prompt_choice('Which map are you playing?', gamemodes[gamemode])
    role = input('Which role are you picking? (e.g. DPS, Support, Tank)\n> ').strip()

    recommender = Recommender(HEROES)
    results = recommender.recommend(role, map_choice, top_n=3)

    if not results:
        print(f'No heroes found for role "{role}". Try another role or add heroes to the dataset.')
        return

    print(f'Top {len(results)} heroes for role "{role}" on {map_choice}:')
    for i, (hero, score) in enumerate(results, start=1):
        print(f'{i}. {hero.name} — score: {score}')


if __name__ == '__main__':
    main()