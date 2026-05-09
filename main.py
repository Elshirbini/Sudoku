"""
main.py — Sudoku Desktop App Entry Point.

Clean, minimal UI modeled after top mobile Sudoku apps.
  • 9×9 interactive grid with dynamic highlighting for rows/cols/boxes and identical numbers.
  • Number pad (1-9) with completion tracking.
  • Action bar: Undo, Erase, Reset, New Game.
  • Intelligent cell feedback (error backgrounds, blue text for user inputs).
"""

from __future__ import annotations

import sys
import time
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, ttk
from typing import Callable, Any

from board import Board
from generator import generate_puzzle
from algorithms import ALGORITHM_MAP


#  Theme constants (Light / Minimal)


class Theme:
    # Backgrounds
    BG_ROOT       = "#FFFFFF"
    
    # Grid Backgrounds
    CELL_EMPTY    = "#FFFFFF"
    CELL_SELECTED = "#A2D5F2"  
    CELL_RELATED  = "#E2EBF3"  
    CELL_MATCH    = "#CBDBED"  
    CELL_ERROR_BG = "#F7CFD6"  
    
    # Text Colors
    TXT_PRIMARY   = "#344861"  
    TXT_FIXED     = "#344861"  
    TXT_USER      = "#4A75B9"  
    TXT_ERROR     = "#E55C6C"  
    TXT_MUTED     = "#ADB5BD"  
    
    # Borders
    BORDER_OUTER  = "#344861"  
    BORDER_INNER  = "#BFC6D4"  
    
    # Buttons & UI
    BTN_BG        = "#F8F9FA"
    BTN_HOVER     = "#E9ECEF"
    BTN_FG        = "#495057"
    
    # Numpad specifics
    NUM_BG        = "#FFFFFF"  
    NUM_FG        = "#295AA4"  
    NUM_USED      = "#FFFFFF"  
    NUM_USED_FG   = "#868E96"  
    
    # Fonts
    FONT_TITLE    = ("Helvetica Neue", 28, "bold")
    FONT_SUBTITLE = ("Helvetica Neue", 14)
    FONT_CELL     = ("Helvetica", 28)                
    FONT_FIXED    = ("Helvetica", 28)                
    FONT_BTN      = ("Helvetica Neue", 11, "bold")
    FONT_NUMPAD   = ("Helvetica", 26, "bold")



#  Utility: rounded button (Canvas-based for custom look)


class RoundedButton(tk.Canvas):
    """A canvas-drawn button with rounded corners and hover animation."""

    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        command: Callable,
        width: int = 60,
        height: int = 60,
        bg: str = Theme.BTN_BG,
        hover_bg: str = Theme.BTN_HOVER,
        fg: str = Theme.BTN_FG,
        font: tuple = Theme.FONT_BTN,
        radius: int = 12,
        canvas_bg: str = Theme.BG_ROOT,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=canvas_bg,
            highlightthickness=0,
            **kwargs,
        )
        self._bg = bg
        self._hover_bg = hover_bg
        self._fg = fg
        self._Original_fg = fg # Keep track of assigned foreground
        self._font = font
        self._radius = radius
        self._text = text
        self._command = command
        self._btn_w = width
        self._btn_h = height
        self._current_color = bg
        self._active = True

        self.after_idle(lambda: self._draw(bg, self._fg))

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _on_enter(self, e: Any) -> None:
        if self._active:
            self._draw(self._hover_bg, self._Original_fg)

    def _on_leave(self, e: Any) -> None:
        if self._active:
            self._draw(self._bg, self._Original_fg)

    def _on_press(self, e: Any) -> None:
        if self._active:
            self._draw(self._bg, self._Original_fg)
            if self._command:
                self._command()

    def _on_release(self, e: Any) -> None:
        if self._active:
            # We are still within widget, handle leave/enter naturally
            # Just redraw hover state when released.
            self._draw(self._hover_bg, self._Original_fg)

    def _draw(self, bg_color: str, fg_color: str) -> None:
        self._current_color = bg_color
        self.delete("all")
        r = self._radius
        w, h = self._btn_w, self._btn_h
        self.create_polygon(
            r, 0,  w - r, 0,
            w, 0,  w, r,
            w, h - r,  w, h,
            w - r, h,  r, h,
            0, h,  0, h - r,
            0, r,  0, 0,
            smooth=True,
            fill=bg_color,
            outline="",
        )
        self.create_text(
            w // 2, h // 2,
            text=self._text,
            fill=fg_color,
            font=self._font,
            justify=tk.CENTER
        )

    def set_state(self, active: bool, dim_bg: str = Theme.NUM_USED, dim_fg: str = Theme.NUM_USED_FG) -> None:
        """Dim (disable) or restore (enable) the button."""
        self._active = active
        if active:
            self._draw(self._bg, self._Original_fg)
        else:
            self._draw(dim_bg, dim_fg)


#  Main Application

class SudokuApp:
    """Full Sudoku desktop application."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.board: Board | None = None
        self.difficulty = tk.StringVar(value="Easy")
        self.algorithm = tk.StringVar(value="Backtracking")
        self.solution_type = "backtracking"

        # Widget references
        self.cells: list[list[tuple[tk.Frame, tk.Label, tk.StringVar]]] = []

        self._configure_root()
        self._build_ui()
        self._new_game()

    def _configure_root(self) -> None:
        self.root.title("Sudoku")
        self.root.configure(bg=Theme.BG_ROOT)

        # Set default window size in case user exits fullscreen
        self.root.update_idletasks()
        w, h = 600, 850
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        
        # Open in fullscreen by default
        self.root.attributes("-fullscreen", True)
        
        # Allow hitting Escape to exit fullscreen
        self.root.bind("<Escape>", lambda event: self.root.attributes("-fullscreen", False))


    # UI Construction

    def _build_ui(self) -> None:
        main_container = tk.Frame(self.root, bg=Theme.BG_ROOT)
        # Using expand=True without fill ensures the board is perfectly centered in fullscreen
        main_container.pack(expand=True, padx=10, pady=5)

        # Header 
        header = tk.Frame(main_container, bg=Theme.BG_ROOT)
        header.pack(fill=tk.X, pady=(5, 10))

        tk.Label(
            header,
            text="Sudoku",
            font=Theme.FONT_TITLE,
            fg=Theme.TXT_PRIMARY,
            bg=Theme.BG_ROOT,
        ).pack(side=tk.LEFT)

        # Difficulty Menu
        diff_menu = tk.OptionMenu(
            header,
            self.difficulty,
            "Easy", "Medium", "Hard",
            command=self._on_diff_change
        )
        diff_menu.config(
            bg=Theme.BG_ROOT, fg=Theme.TXT_PRIMARY, font=Theme.FONT_SUBTITLE,
            highlightthickness=0, indicatoron=0, bd=0, activebackground=Theme.BG_ROOT, activeforeground=Theme.TXT_USER
        )
        diff_menu["menu"].config(bg=Theme.BG_ROOT, fg=Theme.TXT_PRIMARY, font=Theme.FONT_SUBTITLE)
        diff_menu.pack(side=tk.RIGHT, pady=8, padx=5)

        # Algorithm Menu
        algo_menu = tk.OptionMenu(
            header,
            self.algorithm,
            *ALGORITHM_MAP.keys()
        )
        algo_menu.config(
            bg=Theme.BG_ROOT, fg=Theme.TXT_PRIMARY, font=Theme.FONT_SUBTITLE,
            highlightthickness=0, indicatoron=0, bd=0, activebackground=Theme.BG_ROOT, activeforeground=Theme.TXT_USER
        )
        algo_menu["menu"].config(bg=Theme.BG_ROOT, fg=Theme.TXT_PRIMARY, font=Theme.FONT_SUBTITLE)
        algo_menu.pack(side=tk.RIGHT, pady=8, padx=5)

        # Grid 
        grid_container = tk.Frame(main_container, bg=Theme.BG_ROOT)
        grid_container.pack(anchor=tk.N)

        outer = tk.Frame(
            grid_container,
            bg=Theme.BORDER_OUTER,
            bd=0,
            highlightthickness=2,
            highlightbackground=Theme.BORDER_OUTER,
        )
        outer.pack()
        self._build_cell_grid(outer)

        # Action Bar
        action_bar = tk.Frame(main_container, bg=Theme.BG_ROOT)
        action_bar.pack(fill=tk.X, pady=(15, 10))
        
        # Center the action buttons
        action_inner = tk.Frame(action_bar, bg=Theme.BG_ROOT)
        action_inner.pack()

        actions = [
            ("⟳ New Game", self._new_game),
            ("▶ Solve", self._solve),
        ]
        
        for text, cmd in actions:
            btn = RoundedButton(
                action_inner, text=text, command=cmd,
                width=120, height=45, radius=8,
                bg=Theme.BTN_BG, hover_bg=Theme.BTN_HOVER, fg=Theme.BTN_FG,
                font=Theme.FONT_BTN
            )
            btn.pack(side=tk.LEFT, padx=15)

    def _build_cell_grid(self, parent: tk.Frame) -> None:
        self.cells = []
        for r in range(9):
            self.cells.append([None] * 9) # type: ignore
            
        parent.config(bg=Theme.BORDER_OUTER, highlightthickness=3, highlightbackground=Theme.BORDER_OUTER, bd=0)

        for br in range(3):
            for bc in range(3):
                # The 3x3 container that handles thin internal borders
                box = tk.Frame(parent, bg=Theme.BORDER_INNER)
                
                # Thick 2-pixel spacing between blocks reveals the BORDER_OUTER parent
                pad_top = 2 if br > 0 else 0
                pad_left = 2 if bc > 0 else 0
                box.grid(row=br, column=bc, pady=(pad_top, 0), padx=(pad_left, 0))

                for r in range(3):
                    for c in range(3):
                        # Thin 1-pixel spacing between cells reveals BORDER_INNER
                        cell_pad_top = 1 if r > 0 else 0
                        cell_pad_left = 1 if c > 0 else 0
                        
                        frame = tk.Frame(box, bg=Theme.CELL_EMPTY)
                        frame.grid(row=r, column=c, pady=(cell_pad_top, 0), padx=(cell_pad_left, 0))
                        
                        global_r, global_c = br * 3 + r, bc * 3 + c
                        
                        var = tk.StringVar()
                        lbl = tk.Label(
                            frame,
                            textvariable=var,
                            width=2,
                            height=1,
                            font=Theme.FONT_CELL,
                            bg=Theme.CELL_EMPTY,
                            fg=Theme.TXT_PRIMARY,
                            bd=0, highlightthickness=0,
                        )
                        # Padding determines final square size
                        lbl.pack(ipady=10, ipadx=8)

                        self.cells[global_r][global_c] = (frame, lbl, var) # type: ignore

    # Grid Rendering & Highlighting    

    def _render_board(self) -> None:
        """Redraw every cell from self.board.current_board."""
        if not self.board:
            return

        for r in range(9):
            for c in range(9):
                self._render_cell(r, c)

    def _render_cell(self, r: int, c: int) -> None:
        _, lbl, var = self.cells[r][c]
        value = self.board.get_value(r, c)
        is_fixed = self.board.is_fixed(r, c)

        bg_color = Theme.CELL_EMPTY
        font = Theme.FONT_CELL
        fg_color = Theme.TXT_PRIMARY

        # 1. Background Logic
        if value != 0 and value != self.board.solution[r][c]:
            bg_color = Theme.CELL_ERROR_BG

        # 2. Foreground / Font Logic
        if is_fixed:
            fg_color = Theme.TXT_FIXED
            font = Theme.FONT_FIXED
        elif value != 0:
            if value == self.board.solution[r][c]:
                fg_color = Theme.TXT_USER
            else:
                fg_color = Theme.TXT_ERROR

        lbl.config(bg=bg_color, fg=fg_color, font=font)
        var.set("" if value == 0 else str(value))
        


    def _on_diff_change(self, *args: Any) -> None:
        # Prompt to start a new game when difficulty drops down changes
        if messagebox.askyesno("New Game", f"Start a new {self.difficulty.get()} game?"):
            self._new_game()

    
    # Game actions
    

    def _new_game(self) -> None:
        # Note: We solve strictly using our fastest logic algorithm behind the scenes.
        # "Constraint Propagation" generates the internal solution fast without UI elements.
        puzzle, solution = generate_puzzle(
            self.difficulty.get(),
            solution_type=self.solution_type,
        )
        self.board = Board(puzzle, solution)
        self._render_board()

    def _solve(self) -> None:
        if not self.board:
            return
            
        solver = ALGORITHM_MAP.get(self.algorithm.get(), ALGORITHM_MAP["Backtracking"])
        
        start_time = time.time()
        solved, backtracks = solver(self.board.current_board)
        elapsed = time.time() - start_time
        
        if solved:
            self.board.apply_algorithm_solution(solved)
            self._render_board()
        else:
            messagebox.showerror("Error", "No solution found!")



#  Entry point

def main() -> None:
    root = tk.Tk()
    app = SudokuApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
