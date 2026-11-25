from pathlib import Path
from datetime import datetime

path = Path("backend/routers/ai_live.py")
source = path.read_text(encoding="utf-8-sig")

marker = "# ===== BUOC 93.22: AUTO AI REFRESH ====="

if marker in source:
    print("Buoc 93.22 da duoc tich hop.")
    raise SystemExit(0)

backup = path.with_name(
    "ai_live.backup_" +
    datetime.now().strftime("%Y%m%d_%H%M%S") +
    ".py"
)
backup.write_text(source, encoding="utf-8")

addition = '''

# ===== BUOC 93.22: AUTO AI REFRESH =====
import logging
import time

logger = logging.getLogger(__name__)

_auto_ai_stop = threading.Event()
_auto_ai_thread = None
_auto_ai_lock = threading.Lock()


def _auto_ai_loop():
    while not _auto_ai_stop.is_set():
        try:
            ai_status()
        except Exception:
            logger.exception("Auto AI refresh failed")

        _auto_ai_stop.wait(30)


def start_auto_ai_refresh():
    global _auto_ai_thread

    with _auto_ai_lock:
        if _auto_ai_thread is not None and _auto_ai_thread.is_alive():
            return

        _auto_ai_stop.clear()
        _auto_ai_thread = threading.Thread(
            target=_auto_ai_loop,
            name="tronhanh-auto-ai",
            daemon=True,
        )
        _auto_ai_thread.start()


def stop_auto_ai_refresh():
    _auto_ai_stop.set()

    with _auto_ai_lock:
        thread = _auto_ai_thread

    if thread is not None and thread.is_alive():
        thread.join(timeout=5)
'''

path.write_text(source + addition, encoding="utf-8")

print("Da sao luu:", backup)
print("Da bo sung auto AI refresh.")
