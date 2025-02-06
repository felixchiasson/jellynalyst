from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

# Local imports
from .config import Settings
from .database.models import init_db, get_db

app = FastAPI(title="Jellynalyst", version="0.1.0")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Settings
settings = Settings(_env_file='.env')

# Database
async_session = None

@app.on_event("startup")
async def startup_event():
    global async_session
    async_session = await init_db(settings)

@app.get("/")
async def home():
    return templates.TemplateResponse("index.html", {"request": {}})

@app.get("/api/stats")
async def get_stats(db: AsyncSession = Depends(lambda: get_db(async_session))):
    return {"message": "TODO: implement stats"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=37192)
