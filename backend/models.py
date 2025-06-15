from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class PropertyType(str, enum.Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    AGRICULTURAL = "agricultural"

class DeviceType(str, enum.Enum):
    INVERTER = "inverter"
    BATTERY = "battery"
    METER = "meter"
    SENSOR = "sensor"

class DeviceStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ERROR = "error"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firstname = Column(String)
    lastname = Column(String)
    address = Column(String)
    user_image = Column(String, nullable=True)  # URL or path to image
    age = Column(Integer)
    gender = Column(SQLAlchemyEnum(Gender, values_callable=lambda obj: [e.value for e in obj]))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    properties = relationship("Property", back_populates="owner")
    devices = relationship("Device", back_populates="owner")
    power_generations = relationship("PowerGeneration", back_populates="user")
    home_metrics = relationship("MyHome", back_populates="user")

class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    property_name = Column(String)
    property_type = Column(SQLAlchemyEnum(PropertyType, values_callable=lambda obj: [e.value for e in obj]))
    address = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    property_image = Column(String, nullable=True)  # URL or path to image
    property_model = Column(String, nullable=True)  # URL or path to GLTF model
    total_earnings = Column(Float, default=0.0)
    total_generation = Column(Float, default=0.0)
    total_used = Column(Float, default=0.0)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="properties")
    devices = relationship("Device", back_populates="property")
    power_generations = relationship("PowerGeneration", back_populates="property")
    home_metrics = relationship("MyHome", back_populates="property")

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_name = Column(String)
    device_id = Column(String, unique=True)  # External device ID
    device_type = Column(SQLAlchemyEnum(DeviceType, values_callable=lambda obj: [e.value for e in obj]))
    device_status = Column(SQLAlchemyEnum(DeviceStatus, values_callable=lambda obj: [e.value for e in obj]), default=DeviceStatus.INACTIVE)
    device_address = Column(String)
    power_produced = Column(Float, default=0.0)
    device_latitude = Column(Float)
    device_longitude = Column(Float)
    user_id = Column(Integer, ForeignKey("users.id"))
    property_id = Column(Integer, ForeignKey("properties.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Device-specific configuration (stored as JSON)
    config = Column(String)  # JSON string for flexible configuration

    # Relationships
    owner = relationship("User", back_populates="devices")
    property = relationship("Property", back_populates="devices")

# Note: PowerGeneration and MyHome will be stored in InfluxDB
# These models are for reference and API validation only
class PowerGeneration(Base):
    __tablename__ = "power_generations"

    id = Column(Integer, primary_key=True, index=True)
    today_power_generation = Column(Float)
    today_date = Column(DateTime)
    today_earning = Column(Float)
    today_used = Column(Float)
    property_id = Column(Integer, ForeignKey("properties.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    property = relationship("Property", back_populates="power_generations")
    user = relationship("User", back_populates="power_generations")

class MyHome(Base):
    __tablename__ = "my_homes"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    producing = Column(Float)
    consuming = Column(Float)
    charging = Column(Float)
    exporting = Column(Float)
    climate = Column(String)
    rain_percentage = Column(Float)

    # Relationships
    property = relationship("Property", back_populates="home_metrics")
    user = relationship("User", back_populates="home_metrics") 