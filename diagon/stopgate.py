from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Any, Optional, Tuple
import time

@dataclass
class StopConfig:
    max_attempts: int = 99         # effectively "until user gives up"
    deadline_s: float = 0.0        # 0 = no deadline
    show_details: bool = True      # show exception text in the dialog
    title: str = "Action required"

Prompt = Callable[[str, str], str]  # (title, message) -> "retry" | "abort"


def _tk_prompt(title: str, message: str) -> str:
    """Blocking modal Retry/Abort prompt. Returns 'retry' or 'abort'. Falls back to console."""
    try:
        import tkinter as tk
        from tkinter import scrolledtext

        choice = {"val": "abort"}

        root = tk.Tk()
        root.title(title)
        root.attributes("-topmost", True)
        root.resizable(False, False)
        root.geometry("520x260+240+240")

        # Message
        lbl = tk.Label(root, text=message, wraplength=480, justify="left", anchor="w")
        lbl.pack(padx=12, pady=(12, 6), fill="x")

        # Optional details (collapsed by default)
        details_frame = tk.Frame(root)
        details_frame.pack(padx=12, pady=(0, 6), fill="both", expand=True)
        details_box = scrolledtext.ScrolledText(details_frame, height=6, width=60, state="disabled")
        # details text is injected by caller via message; we keep it simple here

        # Buttons
        btn_row = tk.Frame(root)
        btn_row.pack(pady=8)

        def on_retry():
            choice["val"] = "retry"
            root.destroy()

        def on_abort():
            choice["val"] = "abort"
            root.destroy()

        tk.Button(btn_row, text="Retry", width=12, command=on_retry).pack(side="left", padx=6)
        tk.Button(btn_row, text="Abort", width=12, command=on_abort).pack(side="left", padx=6)

        # Focus nudge for macOS
        root.after(50, root.focus_force)
        root.mainloop()
        return choice["val"]
    except Exception:
        # Console fallback
        print(f"[STOP] {title}\n{message}\nType 'r' to retry or anything else to abort: ", end="", flush=True)
        try:
            return "retry" if input().strip().lower() == "r" else "abort"
        except Exception:
            return "abort"


def stop_until_resolved(
    op: Callable[[], Any],
    *,
    prompt: Prompt = _tk_prompt,
    cfg: StopConfig = StopConfig(),
) -> Any:
    """
    Run op(). If it raises, block with a modal 'Retry/Abort' prompt until success or abort.
    No error typing; this is a general 'human-in-the-loop' stopper.
    """
    start = time.monotonic()
    attempts = 0

    while True:
        attempts += 1
        try:
            return op()
        except Exception as e:
            if cfg.deadline_s and (time.monotonic() - start) >= cfg.deadline_s:
                raise RuntimeError("Deadline reached; aborting.") from e
            if attempts >= cfg.max_attempts:
                raise RuntimeError("Max attempts reached; aborting.") from e

            # Compose a concise message (no stack trace, keep it simple)
            msg = (
                "An operation failed.\n\n"
                "Take whatever action is needed outside the program "
                "(e.g., close a file, log in, connect VPN), then click Retry."
                f"\n\nDetails: {type(e).__name__}: {e}"
            )
            action = prompt(cfg.title, msg)
            if action != "retry":
                # user aborted
                raise


def pause_on_error(*, prompt: Prompt = _tk_prompt, cfg: StopConfig = StopConfig()):
    """
    Decorator version. Example:
        @pause_on_error()
        def save(): ...
    """
    def _wrap(fn: Callable[..., Any]) -> Callable[..., Any]:
        def _inner(*args, **kwargs):
            return stop_until_resolved(lambda: fn(*args, **kwargs), prompt=prompt, cfg=cfg)
        return _inner
    return _wrap
