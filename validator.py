"""
Sudoku Validation Module.

All validation logic for Sudoku rules is centralised here.
No imports from other project modules — pure, self-contained logic.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _row_values(board: list[list[int]], row: int) -> list[int]:
    return [board[row][c] for c in range(9) if board[row][c] != 0]


def _col_values(board: list[list[int]], col: int) -> list[int]:
    return [board[r][col] for r in range(9) if board[r][col] != 0]


def _box_values(board: list[list[int]], row: int, col: int) -> list[int]:
    br, bc = (row // 3) * 3, (col // 3) * 3
    return [
        board[r][c]
        for r in range(br, br + 3)
        for c in range(bc, bc + 3)
        if board[r][c] != 0
    ]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def is_valid_move(
    board: list[list[int]],
    row: int,
    col: int,
    num: int,
) -> bool:
    """
    Return True if placing `num` at (row, col) does not violate Sudoku rules.
    The cell at (row, col) is treated as empty when checking.
    """
    if num < 1 or num > 9:
        return False

    # Temporarily zero the cell so its current value doesn't interfere
    original = board[row][col]
    board[row][col] = 0

    row_vals = _row_values(board, row)
    col_vals = _col_values(board, col)
    box_vals = _box_values(board, row, col)

    valid = (
        num not in row_vals
        and num not in col_vals
        and num not in box_vals
    )

    board[row][col] = original
    return valid


def is_board_complete(board: list[list[int]]) -> bool:
    """Return True if every cell is filled (no zeros) and the board is valid."""
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                return False
    return is_board_valid(board)


def is_board_valid(board: list[list[int]]) -> bool:
    """
    Return True if the entire board satisfies all Sudoku constraints.
    Ignores empty cells (value 0).
    """
    # Check rows
    for r in range(9):
        vals = _row_values(board, r)
        if len(vals) != len(set(vals)):
            return False

    # Check columns
    for c in range(9):
        vals = _col_values(board, c)
        if len(vals) != len(set(vals)):
            return False

    # Check 3×3 boxes
    for br in range(0, 9, 3):
        for bc in range(0, 9, 3):
            vals = _box_values(board, br, bc)
            if len(vals) != len(set(vals)):
                return False

    return True


def cell_is_correct(
    solution: list[list[int]],
    row: int,
    col: int,
    value: int,
) -> bool:
    """
    Return True if `value` matches the known solution at (row, col).
    Used for real-time cell feedback in the UI.
    """
    return solution[row][col] == value
