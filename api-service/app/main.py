from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, devices

app = FastAPI(title="FactoryOps API Service")

# CORS - Allow open access for dev testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "api-service"}

# Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(devices.router, prefix="/api/v1")
