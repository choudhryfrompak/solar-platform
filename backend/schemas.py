from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from models import Gender, PropertyType, DeviceType, DeviceStatus

class UserBase(BaseModel):
    firstname: str
    lastname: str
    address: str
    age: int
    gender: Gender
    is_active: bool = True
    user_image: Optional[str] = None

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PropertyBase(BaseModel):
    property_name: str
    property_type: PropertyType
    address: str
    latitude: float
    longitude: float
    property_image: Optional[str] = None
    property_model: Optional[str] = None
    total_earnings: float = 0.0
    total_generation: float = 0.0
    total_used: float = 0.0
    user_id: int

class PropertyCreate(PropertyBase):
    pass

class Property(PropertyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DeviceBase(BaseModel):
    device_name: str
    device_id: str
    device_type: DeviceType
    device_status: DeviceStatus = DeviceStatus.INACTIVE
    device_address: str
    power_produced: float = 0.0
    device_latitude: float
    device_longitude: float
    user_id: int
    property_id: int
    config: Optional[str] = None

class DeviceCreate(DeviceBase):
    pass

class Device(DeviceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PowerGenerationBase(BaseModel):
    today_power_generation: float
    today_date: datetime
    today_earning: float
    today_used: float
    property_id: int
    user_id: int

class PowerGenerationCreate(PowerGenerationBase):
    pass

class PowerGeneration(PowerGenerationBase):
    id: int

    class Config:
        from_attributes = True

class MyHomeBase(BaseModel):
    property_id: int
    user_id: int
    producing: float
    consuming: float
    charging: float
    exporting: float
    climate: str
    rain_percentage: float

class MyHomeCreate(MyHomeBase):
    pass

class MyHome(MyHomeBase):
    id: int

    class Config:
        from_attributes = True 