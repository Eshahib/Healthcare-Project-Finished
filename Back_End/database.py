from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# Use SQLite for local development (no MySQL setup required)
# For production, switch back to MySQL
USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

if USE_SQLITE:
    # SQLite database for local development
    DATABASE_URL = "sqlite:///./symptom_checker.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=True)
else:
    # MySQL for production
    import mysql.connector
    DB_USER = os.getenv("MYSQL_USER")
    DB_PASSWORD = os.getenv("MYSQL_PASSWORD")
    DB_HOST = os.getenv("MYSQL_HOST")
    DB_NAME = os.getenv("MYSQL_DB")
    
    # Connect without specifying database just to create it if it doesn't exist
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Warning: Could not connect to MySQL: {e}")
        print("Falling back to SQLite for local development...")
        DATABASE_URL = "sqlite:///./symptom_checker.db"
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=True)
    else:
        DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
        engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def getDB():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
