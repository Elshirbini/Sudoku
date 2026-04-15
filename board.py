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

        # Undo stack — each entry is (row, col, previous_value)
        self._undo_stack: list[tuple[int, int, int]] = []

    # ------------------------------------------------------------------
    # Fixed-cell queries
    # ------------------------------------------------------------------

    def is_fixed(self, row: int, col: int) -> bool:
        """Return True if (row, col) is a pre-filled clue (not editable)."""
        return self.puzzle[row][col] != 0

    # ------------------------------------------------------------------
    # Move recording
    # ------------------------------------------------------------------

    def record_move(self, row: int, col: int, new_value: int) -> None:
        """
        Record a user edit and apply it to `current_board`.

        Args:
            row:       0-based row index.
            col:       0-based column index.
            new_value: The digit the user entered (0 = cleared).
        """
        if self.is_fixed(row, col):
            return  # Safety guard — fixed cells must never be recorded

        old_value = self.current_board[row][col]
        self._undo_stack.append((row, col, old_value))
        self.current_board[row][col] = new_value

    # ------------------------------------------------------------------
    # Undo
    # ------------------------------------------------------------------

    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    def undo(self) -> tuple[int, int, int] | None:
        """
        Pop the last move from the undo stack and revert `current_board`.

        Returns:
            (row, col, restored_value) so the UI can update the correct cell,
            or None if the stack is empty.
        """
        if not self._undo_stack:
            return None

        row, col, old_value = self._undo_stack.pop()
        self.current_board[row][col] = old_value
        return row, col, old_value

    def clear_undo_stack(self) -> None:
        self._undo_stack.clear()

    # ------------------------------------------------------------------
    # Solve (fill everything from solution)
    # ------------------------------------------------------------------

    def apply_solution(self) -> None:
        """Overwrite current_board with the full solution."""
        self.current_board = [row[:] for row in self.solution]
        self.clear_undo_stack()

    def apply_algorithm_solution(
        self,
        solved: list[list[int]],
    ) -> None:
        """
        Store an algorithm-produced solution (may differ in ordering from
        the canonical solution but is always valid) into current_board.
        """
        self.current_board = [row[:] for row in solved]
        self.clear_undo_stack()

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Restore current_board to the original puzzle state."""
        self.current_board = [row[:] for row in self.puzzle]
        self.clear_undo_stack()

    # ------------------------------------------------------------------
    # Convenience read access
    # ------------------------------------------------------------------

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
