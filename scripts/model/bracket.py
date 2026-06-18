"""Static 48-team bracket topology for the 2026 FIFA World Cup.

The group draw and knockout bracket connectivity are fixed by the pre-tournament
draw and don't change as the tournament progresses -- only which *teams* occupy
each slot changes. Captured once (2026-06-18) from the Wikipedia bracket/R32
placeholder text rather than re-parsed from each day's scrape, because that
placeholder text (e.g. "Winner Match 73") disappears once a slot resolves to
an actual team name, which would make later runs unable to recover it.

Each Round-of-32 slot is a (selector_type, value) pair:
  ("winner", "A")      -> Group A's 1st-place team
  ("runner_up", "A")   -> Group A's 2nd-place team
  ("third", [...])     -> whichever of the listed groups' 3rd-place team is
                           assigned here (see model/simulate.py's bipartite
                           matching of the 8 qualifying 3rd-place teams to
                           these 8 candidate-list slots)
"""

ROUND_OF_32_SLOTS = [
    (("runner_up", "A"), ("runner_up", "B")),
    (("winner", "C"), ("runner_up", "F")),
    (("winner", "E"), ("third", ["A", "B", "C", "D", "F"])),
    (("winner", "F"), ("runner_up", "C")),
    (("runner_up", "E"), ("runner_up", "I")),
    (("winner", "I"), ("third", ["C", "D", "F", "G", "H"])),
    (("winner", "A"), ("third", ["C", "E", "F", "H", "I"])),
    (("winner", "L"), ("third", ["E", "H", "I", "J", "K"])),
    (("winner", "G"), ("third", ["A", "E", "H", "I", "J"])),
    (("winner", "D"), ("third", ["B", "E", "F", "I", "J"])),
    (("winner", "H"), ("runner_up", "J")),
    (("runner_up", "K"), ("runner_up", "L")),
    (("winner", "B"), ("third", ["E", "F", "G", "I", "J"])),
    (("runner_up", "D"), ("runner_up", "G")),
    (("winner", "J"), ("runner_up", "H")),
    (("winner", "K"), ("third", ["D", "E", "I", "J", "L"])),
]

# Each entry indexes into the previous round's results, in that round's order above.
R16_CONNECTIVITY = [(0, 2), (1, 4), (3, 5), (6, 7), (10, 11), (8, 9), (13, 15), (12, 14)]
QF_CONNECTIVITY = [(0, 1), (4, 5), (2, 3), (6, 7)]
SF_CONNECTIVITY = [(0, 1), (2, 3)]
FINAL_CONNECTIVITY = (0, 1)
THIRD_PLACE_CONNECTIVITY = (0, 1)
