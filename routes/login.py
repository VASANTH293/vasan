from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.hash import bcrypt
from database import db

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/signup", response_class=HTMLResponse)
async def signup_form(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@router.post("/signup")
async def signup(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    # check existing user
    existing = await db["users"].find_one({"username": username})
    if existing:
        return templates.TemplateResponse("signup.html", {"request": request, "error": "⚠️ Username already exists"})

    # hash password before storing
    hashed_pw = bcrypt.hash(password)
    await db["users"].insert_one({"username": username, "email": email, "password": hashed_pw})

    return RedirectResponse("/login", status_code=303)
