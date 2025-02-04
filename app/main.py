import os
from typing import List
from datetime import date
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from sqlalchemy.orm import Session
from . import models, schemas, database
from app.scripts import getData


# Setup database if not created
models.Base.metadata.create_all(bind=database.engine)


# Setup background jobs
jobstores = {"default": MemoryJobStore()}
scheduler = AsyncIOScheduler(jobstore=jobstores)


@scheduler.scheduled_job("interval", hours=1)
def pullData():
    print("Getting Data")
    getData.getData()


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
current_file_dir = os.path.dirname(os.path.realpath(__file__))
static_files_dir = os.path.join(current_file_dir, "static")
templates_files_dir = os.path.join(current_file_dir, "templates")

# Mount the static directory
app.mount("/static", StaticFiles(directory=static_files_dir), name="static")
templates = Jinja2Templates(directory=templates_files_dir)


@app.get("/")
async def home(request: Request, db: Session = Depends(database.get_db)):
    latest = db.query(models.Threat).order_by(models.Threat.date.desc()).first()
    return templates.TemplateResponse(
        request=request, name="home.html", context={"last_updated": latest.date}
    )


from fastapi import Query


from fastapi import Query
from datetime import date


@app.get("/view", response_model=List[schemas.Threat])
async def view(
    db: Session = Depends(database.get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1),
    start_date: date = None,
    end_date: date = None,
):
    offset = (page - 1) * limit
    query = db.query(models.Threat)

    if start_date and end_date:
        query = query.filter(
            models.Threat.date >= start_date, models.Threat.date <= end_date
        )
    elif start_date:
        query = query.filter(models.Threat.date >= start_date)
    elif end_date:
        query = query.filter(models.Threat.date <= end_date)

    threats = query.offset(offset).limit(limit).all()
    return threats


@app.get("/download")
async def download(db: Session = Depends(database.get_db)):
    query = db.query(models.Threat).all()  # Fetching all threats from the database

    threats = [schemas.Threat.model_validate(item).model_dump() for item in query]

    # Create a JSONResponse object
    response = JSONResponse(content=threats)

    # Set the headers to prompt a file download
    response.headers["Content-Disposition"] = "attachment; filename=threats.json"
    return response


# Jobs to do after everthing has started
# Fetch data to populate database
getData.getData()
