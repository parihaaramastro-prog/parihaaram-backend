from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from calculate_jathagam import calculate_jathagam
import uvicorn
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow CORS for all origins (simplifies integration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BirthDetails(BaseModel):
    year: int
    month: int
    day: int
    hour: int
    minute: int
    lat: float
    lon: float

@app.get("/")
def read_root():
    return {"status": "active", "service": "Pariharam Astrology Engine"}

@app.post("/calculate")
def calculate(details: BirthDetails):
    try:
        # Call the logic from the existing script
        result = calculate_jathagam(
            details.year, details.month, details.day,
            details.hour, details.minute, details.lat, details.lon
        )
        return result
    except Exception as e:
        print(f"Calculation Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
