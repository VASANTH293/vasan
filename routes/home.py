from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
import requests
from bsedata.bse import BSE
# from database import collection

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# =========================
# NSE API Setup
# =========================
NSE_API = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050"
NSE_HOME = "https://www.nseindia.com/"

headers_nse = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": NSE_HOME,
    "Connection": "keep-alive"
}

def fetch_nse():
    session = requests.Session()
    try:
        home_res = session.get(NSE_HOME, headers=headers_nse, timeout=5)
        res = session.get(NSE_API, headers=headers_nse, cookies=home_res.cookies, timeout=5)
        res.raise_for_status()
        data = res.json()
        stocks = data.get("data", [])
        if not stocks:
            raise ValueError("No data from NSE")
        df = pd.DataFrame(stocks)
        for col in ['symbol','open','dayHigh','dayLow','lastPrice','previousClose','pChange']:
            if col not in df.columns:
                df[col] = 0
        df['pChange'] = df['pChange'].astype(float)
        gainers = df.sort_values("pChange", ascending=False).head(20)
        losers = df.sort_values("pChange", ascending=True).head(20)
        return gainers, losers
    except Exception as e:
        columns = ['symbol','open','dayHigh','dayLow','lastPrice','previousClose','pChange']
        error_df = pd.DataFrame([{**{c: '' for c in columns}, 'symbol': f"NSE API Error: {e}"}])
        return error_df, error_df

def fetch_bse():
    b = BSE(update_codes=True)
    gainers = pd.DataFrame(b.topGainers()).head(20)
    losers = pd.DataFrame(b.topLosers()).head(20)
    return gainers, losers

# -------------------------
# Routes
# -------------------------
@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@router.post("/submit")
async def submit(
    name: str = Form(...),
    phone: str = Form(...),
    whatsapp: str = Form(""),
    insurance: str = Form(...),
    mutualfund: str = Form(...),
    stockresearch: str = Form(...),
    expertcall: str = Form(...)
):
    doc = {
        "name": name,
        "phone": phone,
        "whatsapp": whatsapp,
        "insurance": insurance,
        "mutualfund": mutualfund,
        "stockresearch": stockresearch,
        "expertcall": expertcall
    }
    await collection.insert_one(doc)
    return RedirectResponse(url="/thankyou", status_code=303)

@router.get("/thankyou", response_class=HTMLResponse)
async def thankyou(request: Request):
    return templates.TemplateResponse("thankyou.html", {"request": request})

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    nse_g, nse_l = fetch_nse()
    bse_g, bse_l = fetch_bse()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "nse_g": nse_g.to_html(index=False, classes="table table-striped", border=0),
        "nse_l": nse_l.to_html(index=False, classes="table table-striped", border=0),
        "bse_g": bse_g.to_html(index=False, classes="table table-striped", border=0),
        "bse_l": bse_l.to_html(index=False, classes="table table-striped", border=0),
    })
