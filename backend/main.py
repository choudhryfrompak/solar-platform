# backend/main.py - Updated with Timezone Support
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List, Optional
import docker
import json
import os
import shutil
import logging
from datetime import datetime
from pathlib import Path
from template_manager import TemplateManager
from database import engine
import models
from api import router as api_router
import socket

# Load InfluxDB config from file
def load_influx_config():
    try:
        with open('/app/influx_config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "url": "https://us-east-1-1.aws.cloud2.influxdata.com",
            "token": "your_token_here",
            "org": "solar",
            "bucket": "solar-bucket"
        }

INFLUX_CONFIG = load_influx_config()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://solar_user:solar_password@postgres:5432/solar_platform")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="Solar Platform API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Docker client initialization (optional)
def get_docker_client():
    docker_sock = '/var/run/docker.sock'
    if os.path.exists(docker_sock):
        try:
            return docker.from_env()
        except Exception as e:
            logging.warning(f"Docker client could not be initialized: {e}")
            return None
    else:
        logging.warning("Docker socket not found. Docker features will be disabled.")
        return None

docker_client = get_docker_client()
logger = logging.getLogger(__name__)

# Updated Database Model with Timezone
class Inverter(Base):
    __tablename__ = "inverters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    inverter_type = Column(String)
    region = Column(String)
    timezone = Column(String, default="UTC")  # Added timezone field
    sems_username = Column(String)
    sems_password = Column(String)
    container_id = Column(String, nullable=True)
    status = Column(String, default="inactive")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_update = Column(DateTime, default=datetime.utcnow)
    interval = Column(Integer, default=300)

Base.metadata.create_all(bind=engine)

# Updated Pydantic models
class InverterCreate(BaseModel):
    name: str
    inverter_type: str
    region: str
    timezone: str = "UTC"
    sems_username: str
    sems_password: str
    interval: Optional[int] = 300

class InverterResponse(BaseModel):
    id: int
    name: str
    inverter_type: str
    region: str
    timezone: str
    status: str
    container_id: Optional[str]
    created_at: datetime
    last_update: datetime
    interval: int
    
    class Config:
        from_attributes = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Container Management with Template System
class ContainerManager:
    def __init__(self):
        self.containers_dir = Path("/app/containers")
        self.containers_dir.mkdir(exist_ok=True)
        self.template_manager = TemplateManager()
        self.docker_client = docker_client
        
    def create_container(self, inverter: Inverter):
        if not self.docker_client:
            logger.error("Docker client not available. Cannot create container.")
            raise RuntimeError("Docker client not available.")
        try:
            if not self.template_manager.validate_template(inverter.inverter_type):
                raise ValueError(f"Invalid or missing template: {inverter.inverter_type}")
            
            container_dir = self.containers_dir / f"inverter_{inverter.id}"
            container_dir.mkdir(exist_ok=True)
            
            if not self.template_manager.copy_template_files(inverter.inverter_type, container_dir):
                raise Exception("Failed to copy template files")
            
            # Create config with timezone
            config = {
                "sems": {
                    "username": inverter.sems_username,
                    "password": inverter.sems_password,
                    "region": inverter.region
                },
                "influxdb": INFLUX_CONFIG,
                "settings": {
                    "interval": inverter.interval,
                    "timezone": inverter.timezone
                }
            }
            
            with open(container_dir / "config.json", "w") as f:
                json.dump(config, f, indent=2)
            
            # Build and run
            image_name = f"solar-scraper-{inverter.id}"
            self.docker_client.images.build(path=str(container_dir), tag=image_name, rm=True)
            
            container = self.docker_client.containers.run(
                image_name,
                name=f"solar-scraper-{inverter.id}",
                detach=True,
                restart_policy={"Name": "unless-stopped"}
            )
            
            logger.info(f"Created container {container.id[:12]} for inverter {inverter.name}")
            return container.id
        except Exception as e:
            logger.error(f"Failed to create container: {e}")
            raise
    
    def stop_container(self, container_id: str):
        if not self.docker_client:
            logger.error("Docker client not available. Cannot stop container.")
            return False
        try:
            container = self.docker_client.containers.get(container_id)
            container.stop()
            container.remove()
            return True
        except:
            return False
    
    def get_container_logs(self, container_id: str):
        if not self.docker_client:
            logger.error("Docker client not available. Cannot get logs.")
            return "Docker client not available."
        try:
            container = self.docker_client.containers.get(container_id)
            return container.logs(tail=100).decode('utf-8')
        except:
            return "Container not found"
    
    def get_container_status(self, container_id: str):
        if not self.docker_client:
            logger.error("Docker client not available. Cannot get status.")
            return "not_found"
        try:
            container = self.docker_client.containers.get(container_id)
            return container.status
        except:
            return "not_found"

container_manager = ContainerManager()

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "Solar Platform API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

@app.get("/config/influx")
async def get_influx_config():
    return {
        "url": INFLUX_CONFIG.get('url', ''),
        "org": INFLUX_CONFIG.get('org', ''),
        "bucket": INFLUX_CONFIG.get('bucket', ''),
        "configured": bool(INFLUX_CONFIG.get('token', '').strip())
    }

@app.post("/inverters", response_model=InverterResponse)
async def create_inverter(inverter: InverterCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_inverter = Inverter(**inverter.dict())
    # If Docker is not available, set status to 'inactive' and skip background task
    if not container_manager.docker_client:
        db_inverter.status = "inactive"
        db.add(db_inverter)
        db.commit()
        db.refresh(db_inverter)
        return db_inverter
    db.add(db_inverter)
    db.commit()
    db.refresh(db_inverter)
    background_tasks.add_task(start_container, db_inverter.id)
    return db_inverter

@app.get("/inverters", response_model=List[InverterResponse])
async def list_inverters(db: Session = Depends(get_db)):
    return db.query(Inverter).all()

@app.get("/inverters/{inverter_id}", response_model=InverterResponse)
async def get_inverter(inverter_id: int, db: Session = Depends(get_db)):
    inverter = db.query(Inverter).filter(Inverter.id == inverter_id).first()
    if not inverter:
        raise HTTPException(status_code=404, detail="Inverter not found")
    return inverter

@app.delete("/inverters/{inverter_id}")
async def delete_inverter(inverter_id: int, db: Session = Depends(get_db)):
    inverter = db.query(Inverter).filter(Inverter.id == inverter_id).first()
    if not inverter:
        raise HTTPException(status_code=404, detail="Inverter not found")
    
    if inverter.container_id:
        container_manager.stop_container(inverter.container_id)
    
    db.delete(inverter)
    db.commit()
    return {"message": "Inverter deleted"}

@app.post("/inverters/{inverter_id}/start")
async def start_inverter(inverter_id: int, background_tasks: BackgroundTasks):
    if not container_manager.docker_client:
        raise HTTPException(status_code=400, detail="Docker client not available. Cannot start container.")
    background_tasks.add_task(start_container, inverter_id)
    return {"message": "Starting container"}

@app.post("/inverters/{inverter_id}/stop")
async def stop_inverter(inverter_id: int, db: Session = Depends(get_db)):
    inverter = db.query(Inverter).filter(Inverter.id == inverter_id).first()
    if not inverter or not inverter.container_id:
        raise HTTPException(status_code=404, detail="Container not found")
    
    if container_manager.stop_container(inverter.container_id):
        inverter.status = "inactive"
        inverter.container_id = None
        db.commit()
        return {"message": "Container stopped"}
    
    raise HTTPException(status_code=400, detail="Failed to stop container")

@app.get("/inverters/{inverter_id}/logs")
async def get_logs(inverter_id: int, db: Session = Depends(get_db)):
    inverter = db.query(Inverter).filter(Inverter.id == inverter_id).first()
    if not inverter or not inverter.container_id:
        return {"logs": "No container running"}
    
    logs = container_manager.get_container_logs(inverter.container_id)
    return {"logs": logs}

@app.get("/inverters/{inverter_id}/status")
async def get_status(inverter_id: int, db: Session = Depends(get_db)):
    inverter = db.query(Inverter).filter(Inverter.id == inverter_id).first()
    if not inverter:
        raise HTTPException(status_code=404, detail="Inverter not found")
    
    if not inverter.container_id:
        return {"status": "inactive"}
    
    status = container_manager.get_container_status(inverter.container_id)
    return {"status": status}

@app.get("/templates")
async def list_templates():
    return {"templates": container_manager.template_manager.list_templates()}

@app.get("/templates/{template_name}")
async def get_template(template_name: str):
    template = container_manager.template_manager.load_template(template_name)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

async def start_container(inverter_id: int):
    db = SessionLocal()
    try:
        inverter = db.query(Inverter).filter(Inverter.id == inverter_id).first()
        if not inverter:
            return
        
        if inverter.container_id:
            container_manager.stop_container(inverter.container_id)
        
        container_id = container_manager.create_container(inverter)
        inverter.container_id = container_id
        inverter.status = "active"
        inverter.last_update = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        logger.error(f"Failed to start container: {e}")
        if inverter:
            inverter.status = "error"
            db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)