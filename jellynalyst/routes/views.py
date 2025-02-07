from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/")
async def home(request: Request):
    """Main page view"""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
        }
    )
