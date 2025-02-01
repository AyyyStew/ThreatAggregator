from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def home():
    return {"msg": "Hello World"}
