"""
Algorithm 5: Constraint Propagation (Naked + Hidden Singles) + Backtracking.

Before falling back to search, exhaustively apply two deterministic rules:

  1. **Naked Single**: If a cell has only one candidate value left → assign it.
  2. **Hidden Single**: If within a row/column/box only one cell can hold
     a particular digit → assign it.

These rules can solve easy/medium puzzles without any backtracking at all.
For harder puzzles, constraint propagation maximally reduces the search space
before backtracking kicks in.

This mirrors how expert human solvers approach Sudoku.
"""

from __future__ import annotations
import copy


# ---------------------------------------------------------------------------
# Domain helpers
# ---------------------------------------------------------------------------

def _peers(row: int, col: int) -> list[tuple[int, int]]:
    result: set[tuple[int, int]] = set()
    for c in range(9):
        result.add((row, c))
    for r in range(9):
        result.add((r, col))
    br, bc = (row // 3) * 3, (col // 3) * 3
    for r in range(br, br + 3):
        for c in range(bc, bc + 3):
            result.add((r, c))
    result.discard((row, col))
    return list(result)


def _build_domains(board: list[list[int]]) -> list[list[set[int]]]:
    domains: list[list[set[int]]] = [[set() for _ in range(9)] for _ in range(9)]
    for r in range(9):
        for c in range(9):
            if board[r][c] != 0:
                domains[r][c] = {board[r][c]}
            else:
                used: set[int] = set()
                used.update(board[r][cc] for cc in range(9) if board[r][cc] != 0)
                used.update(board[rr][c] for rr in range(9) if board[rr][c] != 0)
                br, bc = (r // 3) * 3, (c // 3) * 3
                for rr in range(br, br + 3):
                    for cc in range(bc, bc + 3):
                        if board[rr][cc] != 0:
                            used.add(board[rr][cc])
                domains[r][c] = set(range(1, 10)) - used
    return domains


def _assign(
    board: list[list[int]],
    domains: list[list[set[int]]],
    row: int,
    col: int,
    digit: int,
) -> bool:
    """
    Assign `digit` to (row, col) and immediately prune it from all peer domains.
    Returns False if a peer domain becomes empty (contradiction).
    """
    board[row][col] = digit
    domains[row][col] = {digit}
    for pr, pc in _peers(row, col):
        if digit in domains[pr][pc]:
            domains[pr][pc].discard(digit)
            if not domains[pr][pc] and board[pr][pc] == 0:
                return False
    return True


# ---------------------------------------------------------------------------
# Propagation pass
# ---------------------------------------------------------------------------

def _propagate(
    board: list[list[int]],
    domains: list[list[set[int]]],
) -> bool:
    """
    Repeatedly apply Naked Singles and Hidden Singles until no more
    deductions can be made.

    Returns True if the board is still consistent, False on contradiction.
    """
    changed = True
    while changed:
        changed = False

        # --- Naked Singles ---
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0 and len(domains[r][c]) == 1:
                    digit = next(iter(domains[r][c]))
                    if not _assign(board, domains, r, c, digit):
                        return False
                    changed = True
                elif board[r][c] == 0 and len(domains[r][c]) == 0:
                    return False  # Contradiction

        # --- Hidden Singles: rows ---
        for r in range(9):
            for digit in range(1, 10):
                places = [c for c in range(9) if board[r][c] == 0 and digit in domains[r][c]]
                if not places:
                    # Digit must appear but has no placement → contradiction
                    if not any(board[r][c] == digit for c in range(9)):
                        return False
                elif len(places) == 1:
                    if not _assign(board, domains, r, places[0], digit):
                        return False
                    changed = True

        # --- Hidden Singles: columns ---
        for c in range(9):
            for digit in range(1, 10):
                places = [r for r in range(9) if board[r][c] == 0 and digit in domains[r][c]]
                if not places:
                    if not any(board[r][c] == digit for r in range(9)):
                        return False
                elif len(places) == 1:
                    if not _assign(board, domains, places[0], c, digit):
                        return False
                    changed = True

        # --- Hidden Singles: 3×3 boxes ---
        for br in range(0, 9, 3):
            for bc in range(0, 9, 3):
                for digit in range(1, 10):
                    places = [
                        (r, c)
                        for r in range(br, br + 3)
                        for c in range(bc, bc + 3)
                        if board[r][c] == 0 and digit in domains[r][c]
                    ]
                    if not places:
                        if not any(
                            board[r][c] == digit
                            for r in range(br, br + 3)
                            for c in range(bc, bc + 3)
                        ):
                            return False
                    elif len(places) == 1:
                        r, c = places[0]
                        if not _assign(board, domains, r, c, digit):
                            return False
                        changed = True

    return True


# ---------------------------------------------------------------------------
# Backtracking (MRV selection + propagation at each node)
# ---------------------------------------------------------------------------

def _select_cell(
    board: list[list[int]],
    domains: list[list[set[int]]],
) -> tuple[int, int] | None:
    best: tuple[int, int] | None = None
    best_size = 10
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                s = len(domains[r][c])
                if s < best_size:
                    best, best_size = (r, c), s
    return best


def _backtrack_cp(
    board: list[list[int]],
    domains: list[list[set[int]]],
    stats: dict,
) -> bool:
    # Propagation before choosing a cell
    if not _propagate(board, domains):
        return False

    cell = _select_cell(board, domains)
    if cell is None:
        return True  # Solved!

    row, col = cell
    if not domains[row][col]:
        return False

    for digit in sorted(domains[row][col]):
        stats["backtracks"] += 1
        # Deep-copy state for this branch
        board_copy = copy.deepcopy(board)
        domains_copy = copy.deepcopy(domains)

        if _assign(board_copy, domains_copy, row, col, digit):
            if _backtrack_cp(board_copy, domains_copy, stats):
                # Write solution back into original board
                for r in range(9):
                    for c in range(9):
                        board[r][c] = board_copy[r][c]
                return True

    return False


def solve(board: list[list[int]]) -> tuple[list[list[int]] | None, int]:
    """
    Solve using Constraint Propagation (Naked + Hidden Singles) + Backtracking.

    Args:
        board: 9×9 grid where 0 represents an empty cell.

    Returns:
        (solved_board, backtracks) if solvable, else (None, backtracks).
    """
    grid = copy.deepcopy(board)
    domains = _build_domains(grid)
    stats: dict = {"backtracks": 0}
    solved = _backtrack_cp(grid, domains, stats)
    return (grid if solved else None, stats["backtracks"])
