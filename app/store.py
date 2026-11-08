"""In-memory jobs; browser work never holds the store lock or API event loop."""

import os
from threading import BoundedSemaphore, Lock

from app import investigator, replay

assessments: dict[str, dict] = {}
links: dict[str, dict] = {}
cache: dict[tuple, dict] = {}
active: set[tuple] = set()
lock = Lock()
slots = BoundedSemaphore(2)
generation = 0


def reset():
    global generation
    with lock:
        generation += 1
        assessments.clear()
        links.clear()
        cache.clear()
        active.clear()


def run_investigation(link_id: str):
    with lock:
        record = links.get(link_id)
        if record is None or record["investigation"] is not None:
            return
        mode = record.get("mode", os.getenv("DEMO_MODE", "replay"))
        key = (record["url"], mode)
        if key in cache:
            record["investigation"] = cache[key]
            return
        if key in active:
            return
        active.add(key)
        version = generation
    try:
        with slots:
            with lock:
                if version != generation:
                    return
            if mode == "replay":
                result = replay.investigate(record["url"])
            elif mode == "live":
                result = investigator.investigate(record["url"])
            else:
                result = {
                    "mode": mode,
                    "status": "failed",
                    "error": "Unknown demo mode.",
                }
        with lock:
            if version == generation:
                cache[key] = result
                for item in links.values():
                    if item["url"] == key[0] and item.get("mode", mode) == mode:
                        item["investigation"] = result
    finally:
        with lock:
            if version == generation:
                active.discard(key)
