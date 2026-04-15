"""
Algorithm 2: Backtracking with Forward Checking.

After assigning a digit to a cell, immediately prune that digit from the
domains (candidate sets) of all peers (same row, column, and 3×3 box).
If any peer's domain becomes empty → failure detected early without
recursing further (constraint propagation one step ahead).

Advantage over pure backtracking: detects dead-ends up to one step early,
significantly reducing the search space.
"""

from __future__ import annotations
import copy


# ---------------------------------------------------------------------------
# Domain helpers
# ---------------------------------------------------------------------------

def _build_domains(board: list[list[int]]) -> list[list[set[int]]]:
    """
    Initialise candidate sets for every cell.
    Fixed cells have a domain of exactly their value; empty cells start
    with {1..9} minus the values already visible in peers.
    """
    domains: list[list[set[int]]] = [[set() for _ in range(9)] for _ in range(9)]

    for r in range(9):
        for c in range(9):
            if board[r][c] != 0:
                domains[r][c] = {board[r][c]}
            else:
                used: set[int] = set()
                # Row peers
                used.update(board[r][cc] for cc in range(9) if board[r][cc] != 0)
                # Column peers
                used.update(board[rr][c] for rr in range(9) if board[rr][c] != 0)
                # Box peers
                br, bc = (r // 3) * 3, (c // 3) * 3
                for rr in range(br, br + 3):
                    for cc in range(bc, bc + 3):
                        if board[rr][cc] != 0:
                            used.add(board[rr][cc])
                domains[r][c] = set(range(1, 10)) - used

    return domains


def _peers(row: int, col: int) -> list[tuple[int, int]]:
    """Return all cells that share a constraint with (row, col)."""
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


# ---------------------------------------------------------------------------
# Solver
# ---------------------------------------------------------------------------

def _find_empty(board: list[list[int]]) -> tuple[int, int] | None:
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                return r, c
    return None


def _backtrack_fc(
    board: list[list[int]],
    domains: list[list[set[int]]],
    stats: dict,
) -> bool:
    cell = _find_empty(board)
    if cell is None:
        return True

    row, col = cell
    for digit in sorted(domains[row][col]):  # iterate over current domain
        # --- assign ---
        board[row][col] = digit
        stats["backtracks"] += 1

        # --- forward check: prune peers ---
        pruned: list[tuple[int, int, int]] = []  # (r, c, removed_digit)
        failure = False
        for pr, pc in _peers(row, col):
            if board[pr][pc] == 0 and digit in domains[pr][pc]:
                domains[pr][pc].discard(digit)
                pruned.append((pr, pc, digit))
                if not domains[pr][pc]:  # domain wipe-out → failure
                    failure = True
                    break

        if not failure and _backtrack_fc(board, domains, stats):
            return True

        # --- undo ---
        board[row][col] = 0
        for pr, pc, d in pruned:
            domains[pr][pc].add(d)

    return False


def solve(board: list[list[int]]) -> tuple[list[list[int]] | None, int]:
    """
    Solve using Backtracking + Forward Checking.

    Args:
        board: 9×9 grid where 0 represents an empty cell.

    Returns:
        (solved_board, backtracks) if solvable, else (None, backtracks).
    """
    grid = copy.deepcopy(board)
    domains = _build_domains(grid)
    stats: dict = {"backtracks": 0}
    solved = _backtrack_fc(grid, domains, stats)
    return (grid if solved else None, stats["backtracks"])
