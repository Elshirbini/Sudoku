"""
Puzzle Generation Module.

Generates a valid, uniquely-solvable Sudoku puzzle at three difficulty levels.

Strategy:
  1. Start with an empty board.
  2. Fill the three independent diagonal 3×3 boxes (no shared constraints).
  3. Solve the remainder with backtracking to produce the full solution.
  4. Remove cells according to difficulty while preserving a unique solution.
"""

from __future__ import annotations
import random

from algorithms import ALGORITHM_MAP
from validator import is_valid_move


# ---------------------------------------------------------------------------
# Difficulty → number of cells to *remove* from the full solution
# ---------------------------------------------------------------------------
DIFFICULTY_REMOVALS: dict[str, int] = {
    "Easy":   36,   # ~45 clues remain
    "Medium": 46,   # ~35 clues remain
    "Hard":   54,   # ~27 clues remain
}

SOLVER_MAP: dict[str, callable] = {
    "backtracking": ALGORITHM_MAP["Backtracking"],
    "forward_checking": ALGORITHM_MAP["Forward Checking"],
    "mrv": ALGORITHM_MAP["MRV Heuristic"],
    "ac3": ALGORITHM_MAP["AC-3 + Backtracking"],
    "constraint_propagation": ALGORITHM_MAP["Constraint Propagation"],
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _empty_board() -> list[list[int]]:
    return [[0] * 9 for _ in range(9)]


def _fill_diagonal_boxes(board: list[list[int]]) -> None:
    """Fill the three independent 3×3 diagonal boxes randomly."""
    for box_start in (0, 3, 6):
        digits = list(range(1, 10))
        random.shuffle(digits)
        idx = 0
        for r in range(box_start, box_start + 3):
            for c in range(box_start, box_start + 3):
                board[r][c] = digits[idx]
                idx += 1


def _solve_board(board: list[list[int]]) -> bool:
    """
    In-place backtracking solver used *only* during generation.
    Returns True when the board is fully solved.
    """
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                digits = list(range(1, 10))
                random.shuffle(digits)  # Randomise for puzzle variety
                for d in digits:
                    if is_valid_move(board, r, c, d):
                        board[r][c] = d
                        if _solve_board(board):
                            return True
                        board[r][c] = 0
                return False
    return True


def _count_solutions(board: list[list[int]], limit: int = 2) -> int:
    """
    Count solutions up to `limit` to verify uniqueness.
    Stops early once `limit` is reached for performance.
    """
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                count = 0
                for d in range(1, 10):
                    if is_valid_move(board, r, c, d):
                        board[r][c] = d
                        count += _count_solutions(board, limit)
                        board[r][c] = 0
                        if count >= limit:
                            return count
                return count
    return 1  # No empty cells → this is a complete (unique) solution


def _remove_cells(
    board: list[list[int]],
    removals: int,
) -> list[list[int]]:
    """
    Remove `removals` cells from a complete board while maintaining a
    unique solution. Returns the puzzle (may have fewer removals if
    uniqueness cannot be maintained).
    """
    puzzle = [row[:] for row in board]
    positions = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(positions)

    removed = 0
    for r, c in positions:
        if removed >= removals:
            break
        backup = puzzle[r][c]
        puzzle[r][c] = 0
        if _count_solutions([row[:] for row in puzzle]) == 1:
            removed += 1
        else:
            puzzle[r][c] = backup  # Restore — removal breaks uniqueness

    return puzzle


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_puzzle(
    difficulty: str = "Easy",
    solution_type: str = "backtracking",
) -> tuple[list[list[int]], list[list[int]]]:
    """
    Generate a Sudoku puzzle of the given difficulty.

    Args:
        difficulty: One of "Easy", "Medium", "Hard".
        solution_type: Solver key used to build the full solution.

    Returns:
        (puzzle, solution) — both are independent 9×9 grids.
        `puzzle` contains 0 for empty cells.
        `solution` is the fully solved grid.
    """
    board = _empty_board()
    _fill_diagonal_boxes(board)
    solver = SOLVER_MAP.get(solution_type, SOLVER_MAP["backtracking"])
    solved_board, _ = solver(board)
    if solved_board is None:
        raise ValueError(f"Failed to solve board using solution_type={solution_type!r}")
    board = [row[:] for row in solved_board]

    solution = [row[:] for row in board]
    removals = DIFFICULTY_REMOVALS.get(difficulty, DIFFICULTY_REMOVALS["Easy"])
    puzzle = _remove_cells(board, removals)

    return puzzle, solution
