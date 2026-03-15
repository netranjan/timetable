from fastapi import FastAPI
from scheduler import build_and_solve

app = FastAPI()


@app.get("/")
def home():
    return {"message": "Timetable Generator API Running"}


@app.post("/generate")
def generate(config: dict):

    try:
        result = build_and_solve(config)
        return result

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }