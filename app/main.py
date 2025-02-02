import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from . import models
from .database import engine
from .scripts.getData import getData

# Setup database if not created
models.Base.metadata.create_all(bind=engine)
# Fetch data to populate database
getData()

# Setup background jobs
jobstores = {"default": MemoryJobStore()}
scheduler = AsyncIOScheduler(jobstore=jobstores)


@scheduler.scheduled_job("interval", hours=1)
def pullData():
    print("Getting Data")
    getData()


# Lifespan method. Used to control setup and teardown in fast api applicaiton lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Scheduler Starting")
    scheduler.start()
    yield
    print("Scheduler Stopping")
    scheduler.shutdown()
    print("Scheduler Stopped")


app = FastAPI(lifespan=lifespan)
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
