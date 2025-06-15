from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from models import User, Property, Device, PowerGeneration, MyHome
from schemas import (
    UserCreate, User as UserSchema,
    PropertyCreate, Property as PropertySchema,
    DeviceCreate, Device as DeviceSchema,
    PowerGenerationCreate, PowerGeneration as PowerGenerationSchema,
    MyHomeCreate, MyHome as MyHomeSchema
)
from database import get_db
from influx_config import INFLUX_CONFIG

router = APIRouter()

# User endpoints
@router.post("/users/", response_model=UserSchema)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/users/", response_model=List[UserSchema])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(User).offset(skip).limit(limit).all()

@router.get("/users/{user_id}", response_model=UserSchema)
def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# Property endpoints
@router.post("/properties/", response_model=PropertySchema)
def create_property(property: PropertyCreate, db: Session = Depends(get_db)):
    db_property = Property(**property.dict())
    db.add(db_property)
    db.commit()
    db.refresh(db_property)
    return db_property

@router.get("/properties/", response_model=List[PropertySchema])
def list_properties(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Property).offset(skip).limit(limit).all()

@router.get("/properties/{property_id}", response_model=PropertySchema)
def get_property(property_id: int, db: Session = Depends(get_db)):
    db_property = db.query(Property).filter(Property.id == property_id).first()
    if not db_property:
        raise HTTPException(status_code=404, detail="Property not found")
    return db_property

# Device endpoints
@router.post("/devices/", response_model=DeviceSchema)
def create_device(device: DeviceCreate, db: Session = Depends(get_db)):
    db_device = Device(**device.dict())
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device

@router.get("/devices/", response_model=List[DeviceSchema])
def list_devices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Device).offset(skip).limit(limit).all()

@router.get("/devices/{device_id}", response_model=DeviceSchema)
def get_device(device_id: int, db: Session = Depends(get_db)):
    db_device = db.query(Device).filter(Device.id == device_id).first()
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")
    return db_device

# Power Generation endpoints (using InfluxDB)
@router.get("/power-generation/{property_id}")
def get_power_generation(property_id: int, start_time: datetime = None, end_time: datetime = None):
    if not start_time:
        start_time = datetime.utcnow() - timedelta(days=1)
    if not end_time:
        end_time = datetime.utcnow()

    client = InfluxDBClient(
        url=INFLUX_CONFIG["url"],
        token=INFLUX_CONFIG["token"],
        org=INFLUX_CONFIG["org"]
    )

    query = f'''
    from(bucket: "{INFLUX_CONFIG["bucket"]}")
        |> range(start: {start_time.isoformat()}Z, stop: {end_time.isoformat()}Z)
        |> filter(fn: (r) => r["_measurement"] == "power_generation")
        |> filter(fn: (r) => r["property_id"] == "{str(property_id)}")
        |> group(columns: ["_time"])
        |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
    '''

    try:
        result = client.query_api().query(query)
        records = []
        for table in result:
            for record in table.records:
                values = record.values
                records.append({
                    "timestamp": values.get("_time"),
                    "power_generation": values.get("power_generation"),
                    "earning": values.get("earning"),
                    "used": values.get("used")
                })
        
        client.close()
        return records
    except Exception as e:
        client.close()
        raise HTTPException(status_code=500, detail=str(e))

# My Home endpoints (using InfluxDB)
@router.get("/my-home/{property_id}")
def get_home_metrics(property_id: int):
    client = InfluxDBClient(
        url=INFLUX_CONFIG["url"],
        token=INFLUX_CONFIG["token"],
        org=INFLUX_CONFIG["org"]
    )

    query = f'''
    from(bucket: "{INFLUX_CONFIG["bucket"]}")
        |> range(start: -5m)
        |> filter(fn: (r) => r["_measurement"] == "home_metrics")
        |> filter(fn: (r) => r["property_id"] == "{str(property_id)}")
        |> last()
    '''

    try:
        result = client.query_api().query(query)
        if not result:
            client.close()
            raise HTTPException(status_code=404, detail="No home metrics found")

        data = {
            "timestamp": None,
            "producing": None,
            "consuming": None,
            "charging": None,
            "exporting": None,
            "climate": None,
            "rain_percentage": None
        }

        for table in result:
            for record in table.records:
                field = record.get_field()
                value = record.get_value()
                if field == "_time":
                    data["timestamp"] = value
                else:
                    data[field] = value

        if all(v is None for v in data.values()):
            client.close()
            raise HTTPException(status_code=404, detail="No home metrics found")
        
        client.close()
        return data
    except Exception as e:
        client.close()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/power-generation/{property_id}")
def create_power_generation(property_id: int, data: PowerGenerationCreate):
    client = InfluxDBClient(
        url=INFLUX_CONFIG["url"],
        token=INFLUX_CONFIG["token"],
        org=INFLUX_CONFIG["org"]
    )
    write_api = client.write_api(write_options=SYNCHRONOUS)
    
    point = Point("power_generation") \
        .tag("property_id", str(property_id)) \
        .tag("user_id", str(data.user_id)) \
        .field("power_generation", data.today_power_generation) \
        .field("earning", data.today_earning) \
        .field("used", data.today_used) \
        .time(data.today_date)
    
    write_api.write(bucket=INFLUX_CONFIG["bucket"], record=point)
    client.close()
    return {"message": "Data written successfully"}

@router.post("/my-home/{property_id}")
def create_home_metrics(property_id: int, data: MyHomeCreate):
    client = InfluxDBClient(
        url=INFLUX_CONFIG["url"],
        token=INFLUX_CONFIG["token"],
        org=INFLUX_CONFIG["org"]
    )
    write_api = client.write_api(write_options=SYNCHRONOUS)
    
    point = Point("home_metrics") \
        .tag("property_id", str(property_id)) \
        .tag("user_id", str(data.user_id)) \
        .field("producing", data.producing) \
        .field("consuming", data.consuming) \
        .field("charging", data.charging) \
        .field("exporting", data.exporting) \
        .field("climate", data.climate) \
        .field("rain_percentage", data.rain_percentage) \
        .time(datetime.utcnow())
    
    write_api.write(bucket=INFLUX_CONFIG["bucket"], record=point)
    client.close()
    return {"message": "Data written successfully"} 