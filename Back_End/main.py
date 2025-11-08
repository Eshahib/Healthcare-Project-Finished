# main.py
from fastapi import FastAPI, Depends, Request
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
import os
from sqlalchemy.orm import Session
import models
from database import engine, Base, getDB


#import routes here
from routes.SymptomRoutes import router as SymptomRouter
from routes.DiagnosisRoutes import router as DiagnosisRouter
from routes.loginRoutes import router as loginRouter

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created/verified!")

app = FastAPI(title="Symptom Diagnosis API")
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")



app.include_router(SymptomRouter, prefix="/api")
app.include_router(DiagnosisRouter, prefix="/api")
app.include_router(loginRouter, prefix="/api")




@app.get("/")
def root():
    return {"message": "Symptom Diagnosis API is running!"}

@app.get("/health")
def health_check(db: Session = Depends(getDB)):
    try:
        db.execute("SELECT 1")
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "db": str(e)}

@app.on_event("startup")
def startup_event():
    init_db()