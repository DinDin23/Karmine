import logging
import threading
import time

from app.config import settings
from app.database import SessionLocal
from app.services.settlement_service import poll_and_settle

logger = logging.getLogger(__name__)

_stop_event = threading.Event()


def _run() -> None:
    while not _stop_event.is_set():
        db = SessionLocal()
        try:
            poll_and_settle(db)
        except Exception:
            logger.exception("Settlement poll loop failed")
        finally:
            db.close()
        _stop_event.wait(settings.settlement_poll_interval_seconds)


def start() -> None:
    thread = threading.Thread(target=_run, daemon=True, name="settlement-worker")
    thread.start()


def stop() -> None:
    _stop_event.set()
