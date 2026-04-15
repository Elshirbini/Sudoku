"""
Algorithm 1: Pure Backtracking (DFS).

Tries digits 1-9 for each empty cell in left-to-right, top-to-bottom order.
No heuristics applied — simplest baseline solver.

Complexity: O(9^n) worst case, where n = number of empty cells.
"""

from __future__ import annotations
import copy

from validator import is_valid_move


def _find_empty(board: list[list[int]]) -> tuple[int, int] | None:
    """Return the first (row, col) with value 0, or None if board is full."""
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                return r, c
    return None


def _backtrack(board: list[list[int]], stats: dict) -> bool:
    """
    Mutates `board` in-place.
    Returns True when a solution is found, False otherwise.
    """
    cell = _find_empty(board)
    if cell is None:
        return True  # All cells filled → solution found

    row, col = cell
    for digit in range(1, 10):
        if is_valid_move(board, row, col, digit):
            board[row][col] = digit
            stats["backtracks"] += 1
            if _backtrack(board, stats):
                return True
            board[row][col] = 0  # Backtrack

    return False


def solve(board: list[list[int]]) -> tuple[list[list[int]] | None, int]:
    """
    Solve a Sudoku puzzle using pure backtracking.

    Args:
        board: 9×9 grid where 0 represents an empty cell.

    Returns:
        (solved_board, backtracks) if solvable, else (None, backtracks).
    """
    grid = copy.deepcopy(board)
    stats: dict = {"backtracks": 0}
    solved = _backtrack(grid, stats)
    return (grid if solved else None, stats["backtracks"])
