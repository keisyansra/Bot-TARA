"""
FastAPI backend buat Bot TARA -- expose gold.prospect_recommendation
ke Telegram bot (dikerjain temen) dan admin dashboard.

Usage:
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

Test lokal: buka http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.responses import FileResponse

from api.routers import prospects, odp

app = FastAPI(
    title="Bot TARA Backend", 
    version="0.1.0"
)

app.include_router(
    prospects.router, 
    prefix="/api/prospects", 
    tags=["prospects"]
)
app.include_router(
    odp.router, 
    prefix="/api/odp", 
    tags=["odp"]
)


@app.get("/")
def root():
    return {
        "status": "ok", 
        "service": "Bot TARA Backend"
    }

@app.get("/map")
def map_page():
    return FileResponse("webapp/map.html")

# @app.get("/map", response_class=HTMLResponse)
# def map_picker():
#     with open("api/map_picker.html", "r", encoding="utf-8") as f:
#         html = f.read()
#         return HTMLResponse(html)
    