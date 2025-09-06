# Diagon

**Diagon** is an open-source toolkit for data workflows:
- Validation
- Scenario management
- Utilities

🚧 This is an initial placeholder release to reserve the `diagon` package name.
Future versions will expand into a full-featured library.

## Stop gate utility

The `stopgate` module offers a small "pause and retry" wrapper for any operation:

```python
from diagon import stop_until_resolved

def save_report():
    with open("report.csv", "wb") as f:
        f.write(b"a,b\n1,2\n")

stop_until_resolved(save_report)
```

If `save_report` raises an exception, a dialog (or console prompt) asks whether to
retry or abort until the action succeeds.
