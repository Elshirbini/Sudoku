"""
Board State Management Module.

The `Board` class is the single source of truth for the game state.
It owns:
  - `puzzle`        — original given clues (never mutated after init)
  - `solution`      — fully solved grid (hidden from UI)
  - `current_board` — live user progress grid

All undo, hint, and reset operations go through this class.
"""

from __future__ import annotations


class Board:
    """Encapsulates all mutable game state for a Sudoku session."""

    def __init__(
        self,
        puzzle: list[list[int]],
        solution: list[list[int]],
    ) -> None:
        """
        Args:
            puzzle:   9×9 grid with 0s for empty cells (given clues).
            solution: 9×9 fully solved grid corresponding to `puzzle`.
        """
        self.puzzle: list[list[int]] = [row[:] for row in puzzle]
        self.solution: list[list[int]] = [row[:] for row in solution]
        self.current_board: list[list[int]] = [row[:] for row in puzzle]

    # Fixed-cell queries


    def is_fixed(self, row: int, col: int) -> bool:
        """Return True if (row, col) is a pre-filled clue (not editable)."""
        return self.puzzle[row][col] != 0




    # Solve (fill everything from solution)

    def apply_solution(self) -> None:
        """Overwrite current_board with the full solution."""
        self.current_board = [row[:] for row in self.solution]

    def apply_algorithm_solution(
        self,
        solved: list[list[int]],
    ) -> None:
        """
        Store an algorithm-produced solution (may differ in ordering from
        the canonical solution but is always valid) into current_board.
        """
        self.current_board = [row[:] for row in solved]

    # Reset

    def reset(self) -> None:
        """Restore current_board to the original puzzle state."""
        self.current_board = [row[:] for row in self.puzzle]


    # Convenience read access


    def get_value(self, row: int, col: int) -> int:
        return self.current_board[row][col]

    def is_complete(self) -> bool:
        """Return True when every cell matches the solution."""
        return self.current_board == self.solution

    def empty_cells(self) -> list[tuple[int, int]]:
        """Return all (row, col) pairs that are currently empty."""
        return [
            (r, c)
            for r in range(9)
            for c in range(9)
            if self.current_board[r][c] == 0
        ]
