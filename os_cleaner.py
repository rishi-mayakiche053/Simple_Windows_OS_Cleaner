"""Application launcher for ClearSpace.

Keep this file small: backend logic lives in cleaner.py and the interface
lives in ui.py, so either layer can be changed independently.
"""

from cleaner import is_admin, log_event
from ui import main


if __name__ == "__main__":
    log_event(
        "INFO",
        "APPLICATION_STARTUP",
        "ClearSpace started.",
        details={"administrator": is_admin()},
    )
    main()
