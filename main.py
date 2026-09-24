from fastapi import FastAPI,Depends,HTTPException
from database import Base,engine,SessionLocal
from models import Rooms,RentalRequests,Users
from typing import Annotated,Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import models

from router import auth,admin
from router.auth import get_current_user

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(admin.router)

origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://localhost:3000",
    "http://127.0.0.1:3000",

    # Netlify Frontend
    "https://imaginative-salamander-19e46b.netlify.app"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# GET DATABASE: 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

user_dependency = Annotated[dict,Depends(get_current_user)]
db_dependency = Annotated[Session,Depends(get_db)]

class Add_ROOM(BaseModel):
    title : str
    location : str
    description : str
    rent : float
    security_deposit : float
    room_type : str
    bedrooms : int
    bathrooms : int
    available_rooms : int
    facilities : str
    available : bool

class UpdateRoom(BaseModel):
    title: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    rent: Optional[float] = None
    security_deposit: Optional[float] = None
    room_type: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    available_rooms: Optional[int] = None
    facilities: Optional[str] = None
    available: Optional[bool] = None

class Tenant(BaseModel):
    room_id : int
    tenant_id : int


@app.get("/rooms")
def home(db: db_dependency):
    rooms = db.query(Rooms).all()
    return rooms

#===========
#   Owner  #
#===========

@app.post('/add/room')
def AddRoom(user : user_dependency, db : db_dependency, NewRoom : Add_ROOM):
    if user is None or user.get('role') != 'owner':
        raise HTTPException(status_code=401, detail='Failed Authetication')
    

    NewRoonModel = Rooms(
    title=NewRoom.title,
    location=NewRoom.location,
    description=NewRoom.description,
    rent=NewRoom.rent,
    security_deposit=NewRoom.security_deposit,
    room_type=NewRoom.room_type,
    bedrooms=NewRoom.bedrooms,
    bathrooms=NewRoom.bathrooms,
    available_rooms=NewRoom.available_rooms,
    facilities=NewRoom.facilities,
    available=NewRoom.available,
    owner_id = user.get('user_id')
    )
    
    db.add(NewRoonModel)
    db.commit()
    
    return JSONResponse(status_code=201,content={'message':'Room added successfully'})

@app.get('/my/rooms')
def MyRooms(user:user_dependency,db:db_dependency):
    if user is None or user.get('role') != 'owner':
        raise HTTPException(status_code=401, detail='Failed Authetication')
    rooms = db.query(Rooms).filter(Rooms.owner_id == user.get('user_id')).all()
    
    return rooms

@app.put('/edit/my/room/{room_id}')
def EditMyRoom(user : user_dependency, db : db_dependency, room_id : int, Update_Room : UpdateRoom):
    if user is None or user.get('role') != 'owner':
        raise HTTPException(status_code=401, detail='Failed Authetication')
    
    room = db.query(Rooms).filter(Rooms.id == room_id).first()
    
    if room is None:
        raise HTTPException(status_code=404, detail='Room not found')
    
    Update_Model = Update_Room.model_dump(exclude_unset=True)
    
    for key,value in Update_Model.items():
        setattr(room,key,value)
    
    db.commit()
    
    return JSONResponse(status_code=200, content={'message':'Room info updated successfully'})



@app.get('/edit/my/room/{room_id}')
def DetailsMyRoom(user : user_dependency, db : db_dependency, room_id : int):
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authetication')
    
    room = db.query(Rooms).filter(Rooms.id == room_id).first()
    
    if room is None:
        raise HTTPException(status_code=404, detail='Room not found')
    
   
    return room
    


@app.delete('/delete/my/room/{room_id}')
def DeleteMyRoom(user : user_dependency, db : db_dependency, room_id : int):
    if user is None or user.get('role') != 'owner':
        raise HTTPException(status_code=401, detail='Failed Authetication')
    
    room = db.query(Rooms).filter(Rooms.id == room_id).first()
    
    if room is None:
        raise HTTPException(status_code=404, detail='Room not found')
    
    db.delete(room)
    db.commit()
    return JSONResponse(status_code=200, content={'message':'Room deleted successfully'})


@app.get('/show/tenant/request')
def ShowTenantRequest(user: user_dependency, db: db_dependency):

    if user is None or user.get('role') != 'owner':
        raise HTTPException(status_code=401, detail='Failed Authentication')

    request = db.query(RentalRequests).join(Rooms, RentalRequests.room_id == Rooms.id).filter(Rooms.owner_id == user.get('user_id')).all()

    return request


@app.put('/accept/tenant/request/{request_id}')
def AcceptTenantReq(user: user_dependency, db: db_dependency,request_id: int):
    if user is None or user.get('role') != 'owner':
        raise HTTPException(status_code=401,detail='Failed Authentication')

    request = db.query(RentalRequests).join(
        Rooms,
        RentalRequests.room_id == Rooms.id
    ).filter(
        RentalRequests.id == request_id,
        Rooms.owner_id == user.get('user_id')
    ).first()

    if request is None:
        raise HTTPException(status_code=404,detail='Request not found')

    request.status = 'accepted'

    db.commit()

    return JSONResponse(status_code=200,content={'message': 'Tenant request accepted successfully'})
#===========
# Varatiya #
#===========

@app.post('/rental/request/{room_id}')
def RentalRequest(user : user_dependency, db : db_dependency, room_id : int):
    
    if user is None or user.get('role') != 'tenant':
        raise HTTPException(status_code=401, detail='Failed Authetication')
    
    roomId = db.query(Rooms).filter(Rooms.id == room_id).first()
    if roomId is None:
        raise HTTPException(status_code=404, detail='Room not found')
    
    
    

    
       
    tenantModel = RentalRequests(
        room_id =room_id,
        tenant_id = user.get('user_id')
    )
    
    db.add(tenantModel)
    db.commit()
    
    return JSONResponse(status_code=201, content={'message':'Successfully requested'})



@app.put('/cancel/rental/request/{room_id}')
def CancelRentalRequest(user: user_dependency, db: db_dependency, room_id: int):

    if user is None or user.get('role') != 'tenant':
        raise HTTPException(status_code=401, detail='Failed Authetication')

    roomId = db.query(Rooms).filter(Rooms.id == room_id).first()

    if roomId is None:
        raise HTTPException(status_code=404, detail='Room not found')

    rentalreq = db.query(RentalRequests).filter(
        RentalRequests.room_id == room_id,
        RentalRequests.tenant_id == user.get('user_id')
    ).first()

    if rentalreq is None:
        raise HTTPException(status_code=404, detail='Rental request not found')

    rentalreq.status = 'cancelled'

    db.commit()

    return JSONResponse(
        status_code=200,
        content={'message': 'Successfully cancelled'}
    )