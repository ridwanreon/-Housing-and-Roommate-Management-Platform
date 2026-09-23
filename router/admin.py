from fastapi import APIRouter,Depends,HTTPException
from typing import Annotated
from router.auth import get_current_user
from database import SessionLocal
from sqlalchemy.orm import Session
from models import Users,Rooms
from fastapi.responses import JSONResponse
router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session,Depends(get_db)]
user_dependency = Annotated[dict,Depends(get_current_user)]

@router.get('/admin/show/all/owner')
def Admin_show_all_owner(user : user_dependency, db : db_dependency):
    if user is None or user.get('role') != 'admin':
        raise HTTPException(status_code=401, detail="Failed AUthentication")
    owner = db.query(Users).filter(Users.role == 'owner').all()
    return owner

@router.get('/admin/show/all/tenant')
def Admin_Show_All_Tenant(user : user_dependency, db : db_dependency):
    if user is None or user.get('role') != 'admin':
        raise HTTPException(status_code=401, detail="Failed AUthentication")
    
    tenant = db.query(Users).filter(Users.role == 'tenant').all()
    return tenant    

@router.delete('/admin/delete/user/{user_id}')
def Admin_delete_user(user : user_dependency, db : db_dependency, user_id : int):
    if user is None or user.get('role') != 'admin':
        raise HTTPException(status_code=401, detail="Failed AUthentication")
    
    delete_someone = db.query(Users).filter(Users.id == user_id).first()
    
    db.delete(delete_someone)
    db.commit()
    return JSONResponse(status_code=201, content={'message': 'User Deleted Successfully'})

@router.delete('/admin/delete/room/{room_id}')
def Admin_Delete_Room(user : user_dependency, db : db_dependency, room_id : int):
    if user is None or user.get('role') != 'admin':
        raise HTTPException(status_code=401, detail="Failed AUthentication")    
    
    delete_room = db.query(Rooms).filter(Rooms.id == room_id).first()
    
    if delete_room is None:
        raise HTTPException(status_code=404, detail="Wrong input")
    
    db.delete(delete_room)
    db.commit()
    
    return JSONResponse(status_code=200, content={'message':'Deleted successfully'})