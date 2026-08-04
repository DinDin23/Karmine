import asyncio
import threading

from fastapi import WebSocket

_connections: dict[int, WebSocket] = {}
_lock = threading.Lock()
_loop: asyncio.AbstractEventLoop | None = None


def set_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _loop
    _loop = loop


def register(user_id: int, websocket: WebSocket) -> None:
    with _lock:
        _connections[user_id] = websocket


def unregister(user_id: int, websocket: WebSocket) -> None:
    with _lock:
        if _connections.get(user_id) is websocket:
            del _connections[user_id]


def notify(user_id: int, payload: dict) -> None:
    """Thread-safe: callable from the sync worker threads that handle HTTP requests."""
    with _lock:
        websocket = _connections.get(user_id)

    if websocket is None or _loop is None:
        return

    asyncio.run_coroutine_threadsafe(websocket.send_json(payload), _loop)
