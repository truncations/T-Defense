import asyncio
import hashlib
import os
import re
import secrets
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import store
from app.page_guard import router as page_guard_router
from app.recovery import checklist
from app.safety import allowed_url
from app.scenarios import load_scenarios
from app.triage import badge_for, triage
from app.verdict import combine

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title="T-Defense", docs_url=None, redoc_url=None)
app.include_router(page_guard_router)


@app.get("/api/health")
def health():
    return {"status": "ok", "demo_mode": os.getenv("DEMO_MODE", "replay")}


class AssessmentRequest(BaseModel):
    message_id: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=8000)


@app.get("/api/scenarios")
def scenarios():
    return load_scenarios()


@app.post("/api/assess")
def assess(request: AssessmentRequest, background_tasks: BackgroundTasks):
    result = triage(request.text)
    assessment_id = secrets.token_urlsafe(18)
    badge = badge_for(result)
    link_items = []
    for match in re.finditer(r"https?://[^\s<>\"']+", request.text):
        url = match.group().rstrip(".,;!?)")
        link_id = secrets.token_urlsafe(24)
        with store.lock:
            store.links[link_id] = {
                "url": url,
                "sha256": hashlib.sha256(url.encode()).hexdigest(),
                "message_id": request.message_id,
                "mode": os.getenv("DEMO_MODE", "replay"),
                "triage": result,
                "investigation": None,
            }
        link_items.append(
            {
                "link_id": link_id,
                "display_text": url.removeprefix("http://").removeprefix("https://"),
                "check_url": "/check/" + link_id,
            }
        )
        if badge != "no_signs":
            background_tasks.add_task(store.run_investigation, link_id)
    response = {
        "assessment_id": assessment_id,
        "message_id": request.message_id,
        "triage": result,
        "badge": badge,
        "links": link_items,
    }
    with store.lock:
        store.assessments[assessment_id] = response
    return response


def get_link(link_id: str):
    record = store.links.get(link_id)
    if record is None:
        raise HTTPException(
            404, "This demo link expired. Return to Messages and tap again."
        )
    return record


@app.post("/api/links/{link_id}/investigate")
def investigate_link(link_id: str, background_tasks: BackgroundTasks):
    record = get_link(link_id)
    if record["investigation"] is None:
        background_tasks.add_task(store.run_investigation, link_id)
    return {
        "link_id": link_id,
        "status": (record["investigation"] or {}).get("status", "pending"),
    }


@app.get("/api/links/{link_id}/verdict")
def verdict(link_id: str):
    record = get_link(link_id)
    return {"link_id": link_id, **combine(record["triage"], record["investigation"])}


@app.get("/api/links/{link_id}/open")
def open_demo(link_id: str):
    record = get_link(link_id)
    card = combine(record["triage"], record["investigation"])
    if (
        card["status"] != "done"
        or card["verdict"] not in {"looks_fine", "suspicious"}
        or not allowed_url(record["url"])
        or (record["investigation"] or {}).get("download_attempted", False)
    ):
        raise HTTPException(403, "This demo link cannot be opened from its verdict.")
    return RedirectResponse(record["url"], status_code=303)


@app.get("/api/recovery")
def recovery(category: str = Query(default="general", max_length=64)):
    return checklist(category)


@app.get("/api/reset")
def reset():
    store.reset()
    return {"reset": True}


@app.get("/sms-demo")
def phone():
    return FileResponse(ROOT / "static/phone.html")


@app.get("/")
@app.get("/extension")
def extension_dashboard():
    return FileResponse(
        ROOT / "static/extension.html",
        headers={
            "Cache-Control": "no-store",
            "X-Frame-Options": "DENY",
            "Content-Security-Policy": "frame-ancestors 'none'",
        },
    )


@app.get("/extension-lab")
def extension_lab():
    return FileResponse(ROOT / "static/extension-lab.html")


@app.get("/check/{link_id}")
def check_page(link_id: str):
    return FileResponse(ROOT / "static/check.html")


@app.get("/mock/lumora/slow.html")
async def slow_page():
    await asyncio.sleep(30)
    return HTMLResponse("<p>DEMO PAGE – NOT A REAL COMPANY – built for hackUTD</p>")


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
app.mount("/mock", StaticFiles(directory=ROOT / "mock_sites"), name="mock")
