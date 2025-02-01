from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="home.html", context={})


@app.get("/view")
async def view(request: Request):
    with open("data/sample.json", "r") as file:
        data = json.load(file)
    return data


@app.get("/download")
async def download(request: Request):
    return FileResponse(
        path="./data/sample.json", filename="sample.json", media_type="application/json"
    )
