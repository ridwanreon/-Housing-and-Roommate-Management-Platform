from database import Base
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from datetime import datetime


class Users(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firstname = Column(String)
    lastname = Column(String)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    phone = Column(String, unique=True)
    password = Column(String)
    role = Column(String, default="tenant")
    is_active = Column(Boolean, default=True)


class Rooms(Base):

    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    location = Column(String)
    description = Column(String)
    rent = Column(Float)
    security_deposit = Column(Float)
    room_type = Column(String)
    bedrooms = Column(Integer)
    bathrooms = Column(Integer)
    available_rooms = Column(Integer)
    facilities = Column(String)
    available = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    





class RentalRequests(Base):

    __tablename__ = "rental_requests"

    id = Column(Integer, primary_key=True, index=True)

    room_id = Column(Integer, ForeignKey("rooms.id"))
    tenant_id = Column(Integer, ForeignKey("users.id"))

    status = Column(String, default="pending")

    request_date = Column(DateTime, default=datetime.utcnow)


class Roommates(Base):

    __tablename__ = "roommates"

    id = Column(Integer, primary_key=True, index=True)

    room_id = Column(Integer, ForeignKey("rooms.id"))
    tenant_id = Column(Integer, ForeignKey("users.id"))

    joined_date = Column(DateTime, default=datetime.utcnow)