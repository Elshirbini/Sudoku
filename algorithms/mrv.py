"""
Algorithm 3: Backtracking with MRV (Minimum Remaining Values) Heuristic.

Instead of picking the next empty cell in row-major order, always choose the
unassigned cell that has the *fewest* legal values remaining in its domain
(the "most constrained variable" / "fail-first" heuristic).

Tie-breaking: among cells with equal domain size, prefer the one with the
most peers that are already assigned (Degree Heuristic), which tends to
constrain the search space further.

Combines naturally with forward checking for domain maintenance.
"""

from __future__ import annotations
import copy


# ---------------------------------------------------------------------------
# Domain helpers  (same logic as forward_checking.py, duplicated for
# module independence — each algorithm is self-contained)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# MRV cell selector
# ---------------------------------------------------------------------------

def _select_mrv_cell(
    board: list[list[int]],
    domains: list[list[set[int]]],
) -> tuple[int, int] | None:
    """
    Return the empty cell with the smallest domain (MRV).
    Break ties with the Degree Heuristic (most assigned peers).
    Returns None if no empty cells remain.
    """
    best: tuple[int, int] | None = None
    best_size = 10          # larger than any real domain (1..9)
    best_degree = -1

    for r in range(9):
        for c in range(9):
            if board[r][c] != 0:
                continue
            size = len(domains[r][c])
            if size == 0:
                return (r, c)  # wipe-out → forced failure, return immediately
            if size < best_size or (size == best_size):
                # Degree: count assigned peers
                degree = sum(
                    1 for pr, pc in _peers(r, c) if board[pr][pc] != 0
                )
                if size < best_size or degree > best_degree:
                    best, best_size, best_degree = (r, c), size, degree

    return best


# ---------------------------------------------------------------------------
# Solver
# ---------------------------------------------------------------------------

def _backtrack_mrv(
    board: list[list[int]],
    domains: list[list[set[int]]],
    stats: dict,
) -> bool:
    cell = _select_mrv_cell(board, domains)
    if cell is None:
        return True  # No empty cells → solved

    row, col = cell

    # If domain is empty → dead-end (detected without looping)
    if not domains[row][col]:
        return False

    for digit in sorted(domains[row][col]):
        board[row][col] = digit
        stats["backtracks"] += 1

        # Forward checking: prune peers
        pruned: list[tuple[int, int, int]] = []
        failure = False
        for pr, pc in _peers(row, col):
            if board[pr][pc] == 0 and digit in domains[pr][pc]:
                domains[pr][pc].discard(digit)
                pruned.append((pr, pc, digit))
                if not domains[pr][pc]:
                    failure = True
                    break

        if not failure and _backtrack_mrv(board, domains, stats):
            return True

        # Undo
        board[row][col] = 0
        for pr, pc, d in pruned:
            domains[pr][pc].add(d)

    return False


def solve(board: list[list[int]]) -> tuple[list[list[int]] | None, int]:
    """
    Solve using Backtracking + MRV + Degree Heuristic + Forward Checking.

    Args:
        board: 9×9 grid where 0 represents an empty cell.

    Returns:
        (solved_board, backtracks) if solvable, else (None, backtracks).
    """
    grid = copy.deepcopy(board)
    domains = _build_domains(grid)
    stats: dict = {"backtracks": 0}
    solved = _backtrack_mrv(grid, domains, stats)
    return (grid if solved else None, stats["backtracks"])
