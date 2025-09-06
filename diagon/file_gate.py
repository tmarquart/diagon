from __future__ import annotations

"""Utility functions for gated file writing with optional Tk dialogs."""

from pathlib import Path
from tempfile import NamedTemporaryFile
import os
from typing import Optional, Union

try:  # pragma: no cover - display availability varies
    import tkinter as tk
except Exception:  # pragma: no cover - tkinter may not be installed
    tk = None  # type: ignore

__all__ = ["tk_toast", "tk_prompt", "gate_write"]


def _center(win: "tk.Tk") -> None:
    """Center ``win`` on the screen."""
    win.update_idletasks()
    width = win.winfo_width()
    height = win.winfo_height()
    x = win.winfo_screenwidth() // 2 - width // 2
    y = win.winfo_screenheight() // 2 - height // 2
    win.geometry(f"{width}x{height}+{x}+{y}")


def tk_toast(message: str, title: str | None = None, *, duration_ms: int = 1500) -> None:
    """Show a brief toast message.

    Falls back to printing on the console when :mod:`tkinter` is unavailable.
    """
    if tk is None:
        print(message)
        return
    try:
        root = tk.Tk()
    except Exception:
        print(message)
        return
    root.withdraw()
    win = tk.Toplevel(root)
    if title:
        win.title(title)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.after(50, win.focus_force)
    win.after(duration_ms, root.destroy)
    tk.Label(win, text=message, padx=10, pady=5).pack()
    win.resizable(False, False)
    _center(win)
    root.mainloop()


def tk_prompt(message: str, title: str | None = None) -> Optional[str]:
    """Prompt the user for text input.

    Returns ``None`` if the user cancels. Falls back to ``input`` when
    :mod:`tkinter` is unavailable.
    """
    if tk is None:
        try:
            return input(f"{message}\n> ")
        except EOFError:
            return None
    try:
        root = tk.Tk()
    except Exception:
        try:
            return input(f"{message}\n> ")
        except EOFError:
            return None
    root.title(title or "Input")
    root.attributes("-topmost", True)
    root.resizable(False, False)
    root.after(50, root.focus_force)

    var = tk.StringVar()
    tk.Label(root, text=message, padx=10, pady=5).pack()
    entry = tk.Entry(root, textvariable=var)
    entry.pack(padx=10, pady=5)
    entry.focus_set()

    result: list[str] = []

    def _ok() -> None:
        result.append(var.get())
        root.destroy()

    def _cancel() -> None:
        root.destroy()

    btns = tk.Frame(root)
    btns.pack(pady=5)
    tk.Button(btns, text="OK", command=_ok).pack(side="left", padx=5)
    tk.Button(btns, text="Cancel", command=_cancel).pack(side="left", padx=5)

    _center(root)
    root.mainloop()
    return result[0] if result else None


def _atomic_replace(path: Path, data: bytes) -> None:
    """Atomically replace ``path`` with ``data``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("wb", delete=False, dir=str(path.parent)) as tmp:
        tmp.write(data)
        tmp.flush()
        os.fsync(tmp.fileno())
    os.replace(tmp.name, path)


def gate_write(path: Union[str, Path], content: str, *, encoding: str = "utf-8") -> Optional[Path]:
    """Prompt the user for a path and write ``content`` atomically.

    Parameters
    ----------
    path:
        Suggested output path.
    content:
        Text content to write.
    encoding:
        File encoding used when writing ``content``.

    Returns
    -------
    Path or ``None``
        The written path, or ``None`` if the user cancels.
    """
    target = tk_prompt(f"Write file to:\n{path}", title="Write File")
    if target is None:
        tk_toast("Write cancelled")
        return None
    dest = Path(target).expanduser()
    _atomic_replace(dest, content.encode(encoding))
    tk_toast(f"Wrote {dest}")
    return dest
