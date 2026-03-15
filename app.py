from fastapi import FastAPI
from scheduler import build_and_solve

app = FastAPI()


@app.post("/generate-timetable")
async def generate_timetable(config: dict):

    try:
        result = build_and_solve(config)
        return result

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }