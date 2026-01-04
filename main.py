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

API_SECRET = os.environ.get("API_SECRET")

from fastapi import Request, status
from fastapi.responses import JSONResponse

@app.middleware("http")
async def check_api_header(request: Request, call_next):
    # Skip check for root endpoint (health check)
    if request.url.path == "/":
        return await call_next(request)

    if not API_SECRET:
        print("Warning: API_SECRET not set in environment. Skipping security check.")
        return await call_next(request)

    client_secret = request.headers.get("x-api-secret")
    if client_secret != API_SECRET:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Invalid or missing API Secret"}
        )
    
    response = await call_next(request)
    return response

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

# --- SMTP / OTP Logic ---
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import BackgroundTasks

SMTP_EMAIL = os.environ.get("SMTP_EMAIL")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

class OTPRequest(BaseModel):
    email: str

def send_email_background(email_to: str, otp: str):
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("SMTP Credentials not set")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = email_to
        msg['Subject'] = "Your Pariharam Verification Code"

        body = f"""
        <html>
            <body style="font-family: sans-serif;">
                <h2>Pariharam Verification</h2>
                <p>Your OTP code is:</p>
                <h1 style="color: #4F46E5; font-size: 32px; letter-spacing: 5px;">{otp}</h1>
                <p>This code will expire in 10 minutes.</p>
            </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SMTP_EMAIL, email_to, text)
        server.quit()
        print(f"OTP sent to {email_to}")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")

# Simple in-memory store for demo purposes (Use Redis/DB in production)
otp_store = {}

@app.post("/send-otp")
async def send_otp(request: OTPRequest, background_tasks: BackgroundTasks):
    otp = "".join([str(random.randint(0, 9)) for _ in range(6)])
    # Store OTP (simple overwrite)
    otp_store[request.email] = otp
    
    background_tasks.add_task(send_email_background, request.email, otp)
    return {"message": "OTP processing", "status": "sent"}

class OTPVerify(BaseModel):
    email: str
    otp: str

@app.post("/verify-otp")
def verify_otp(request: OTPVerify):
    if request.email not in otp_store:
        raise HTTPException(status_code=400, detail="No OTP found for this email")
    
    if otp_store[request.email] == request.otp:
        del otp_store[request.email] # OTP used
        return {"status": "success", "message": "Verified successfully"}
    
    raise HTTPException(status_code=400, detail="Invalid OTP")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
