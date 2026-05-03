"""
Algorithm 4: AC-3 (Arc Consistency 3) + Backtracking.

AC-3 enforces arc consistency across all constraint pairs:
  For every arc (Xi, Xj) in the constraint graph, remove from Xi's domain
  any value for which there is no consistent value in Xj's domain.

After AC-3 reduces domains upfront (and during search), backtracking is
applied on the remaining search space. This is more powerful than simple
forward checking because AC-3 propagates constraints transitively.

Time complexity of a single AC-3 pass: O(ed³) where e = arcs, d = domain size.
"""

from __future__ import annotations
import copy
from collections import deque



# Constraint graph helpers

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


def _build_arcs() -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """Return all directed arcs (Xi, Xj) for every constraint pair."""
    arcs: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for r in range(9):
        for c in range(9):
            for pr, pc in _peers(r, c):
                arcs.append(((r, c), (pr, pc)))
    return arcs


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



# AC-3 core

def _revise(
    domains: list[list[set[int]]],
    xi: tuple[int, int],
    xj: tuple[int, int],
) -> bool:
    """
    Remove from domains[xi] any value with no support in domains[xj].
    Returns True if the domain of xi was revised (reduced).

    Sudoku constraint: xi ≠ xj  →  a value v in Xi has support iff
    there exists some w ≠ v in Xj's domain.
    """
    xi_r, xi_c = xi
    xj_r, xj_c = xj

    to_remove: set[int] = set()
    for v in domains[xi_r][xi_c]:
        # Support exists if Xj has *some* value != v
        if domains[xj_r][xj_c] - {v} == set():
            to_remove.add(v)

    if to_remove:
        domains[xi_r][xi_c] -= to_remove
        return True

    return False


def _ac3(domains: list[list[set[int]]]) -> bool:
    """
    Run AC-3 algorithm over all arcs.
    Returns False if any domain becomes empty (no solution possible).
    Mutates `domains` in-place.
    """
    queue: deque[tuple[tuple[int, int], tuple[int, int]]] = deque(_build_arcs())

    while queue:
        xi, xj = queue.popleft()
        if _revise(domains, xi, xj):
            xi_r, xi_c = xi
            if not domains[xi_r][xi_c]:
                return False  # Domain wipe-out
            # Re-add arcs (Xk, Xi) for Xk in peers of Xi (excluding Xj)
            for pk, pc in _peers(xi_r, xi_c):
                if (pk, pc) != xj:
                    queue.append(((pk, pc), xi))

    return True



# MRV cell selector

def _select_cell(
    board: list[list[int]],
    domains: list[list[set[int]]],
) -> tuple[int, int] | None:
    """
    Return the unassigned cell with the fewest remaining values (MRV).
    Returns None if no empty cells remain.
    """
    best: tuple[int, int] | None = None
    best_size = 10
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                s = len(domains[r][c])
                if s < best_size:
                    best, best_size = (r, c), s
    return best



# Backtracking with full domain snapshot per branch


def _backtrack(
    board: list[list[int]],
    domains: list[list[set[int]]],
    stats: dict,
) -> bool:
    """
    Backtracking search with AC-3 propagation at each node.

    Key correctness guarantee: AC-3 propagates transitively across the
    *entire* board, not just the direct peers of the assigned cell.
    A partial (peer-only) snapshot would therefore leave a corrupt domain
    state on backtrack.  We deep-copy the full domain grid before every
    assignment so rollback is always complete and correct.
    """
    cell = _select_cell(board, domains)
    if cell is None:
        return True  # No empty cells → solved

    row, col = cell
    if not domains[row][col]:
        return False  # Domain wipe-out detected

    for digit in sorted(domains[row][col]):
        stats["backtracks"] += 1

        # --- Branch: deep-copy everything before assignment + AC-3 ---
        board_copy = copy.deepcopy(board)
        domains_copy = copy.deepcopy(domains)

        board_copy[row][col] = digit
        domains_copy[row][col] = {digit}

        # Propagate via AC-3
        consistent = _ac3(domains_copy)

        if consistent:
            # Sync any singleton domains produced by AC-3 back onto the
            # board so board and domains stay consistent
            for r in range(9):
                for c in range(9):
                    if board_copy[r][c] == 0 and len(domains_copy[r][c]) == 1:
                        board_copy[r][c] = next(iter(domains_copy[r][c]))

            if _backtrack(board_copy, domains_copy, stats):
                # Propagate the solution back to the caller's board
                for r in range(9):
                    board[r] = board_copy[r]
                return True

        # No explicit undo needed — board/domains_copy are discarded

    return False



# Public API

def solve(board: list[list[int]]) -> tuple[list[list[int]] | None, int]:
    """
    Solve using AC-3 (Arc Consistency 3) + Backtracking.

    Args:
        board: 9×9 grid where 0 represents an empty cell.

    Returns:
        (solved_board, backtracks) if solvable, else (None, backtracks).
    """
    grid = copy.deepcopy(board)
    domains = _build_domains(grid)
    stats: dict = {"backtracks": 0}

    # Initial AC-3 pass — may already solve simple/medium puzzles fully
    if not _ac3(domains):
        return None, 0

    # Apply singleton domains from the initial AC-3 pass to the board
    for r in range(9):
        for c in range(9):
            if grid[r][c] == 0 and len(domains[r][c]) == 1:
                grid[r][c] = next(iter(domains[r][c]))

    solved = _backtrack(grid, domains, stats)
    return (grid if solved else None, stats["backtracks"])
