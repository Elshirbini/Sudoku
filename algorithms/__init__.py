"""
Sudoku AI Algorithms Package.

Each module exposes a single public function:
    solve(board: list[list[int]]) -> list[list[int]] | None

Where `board` is a 9×9 grid (0 = empty cell) and the return value is
the fully solved grid, or None if no solution exists.
"""

from algorithms.backtracking import solve as backtracking_solve
from algorithms.forward_checking import solve as forward_checking_solve
from algorithms.mrv import solve as mrv_solve
from algorithms.ac3 import solve as ac3_solve
from algorithms.constraint_propagation import solve as constraint_propagation_solve

ALGORITHM_MAP: dict[str, callable] = {
    "Backtracking": backtracking_solve,
    "Forward Checking": forward_checking_solve,
    "MRV Heuristic": mrv_solve,
    "AC-3 + Backtracking": ac3_solve,
    "Constraint Propagation": constraint_propagation_solve,
}

__all__ = [
    "ALGORITHM_MAP",
    "backtracking_solve",
    "forward_checking_solve",
    "mrv_solve",
    "ac3_solve",
    "constraint_propagation_solve",
]
