from fastapi import APIRouter,Depends,HTTPException
from database import SessionLocal
from typing import Annotated,Optional,Literal
from sqlalchemy.orm import Session
from pydantic import BaseModel,Field
from models import Users
from passlib.context import CryptContext
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from datetime import timedelta,datetime,timezone
from jose import jwt
router = APIRouter()


bcrypt_context = CryptContext(schemes=['bcrypt'],deprecated = 'auto')
Oauth2_bearer = OAuth2PasswordBearer(tokenUrl='login')

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session,Depends(get_db)]


SECRET_KEY = '6cd0112bdb79b73067eef8435e980aaf006c0a99465fe397185b0e6bf10aebfd'
ALGORITHM = 'HS256'


class CreateUser(BaseModel):
    firstname: str
    lastname : str
    username : str
    email : str 
    phone : str  = Field(min_length=11, max_length=11)
    password : str = Field(min_length=8)
    role: Literal["tenant", "owner","admin"]

class UpdateUser(BaseModel):
    firstname : Optional[str] = Field(default=None)
    lastname : Optional[str] = Field(default=None)
    username : Optional[str] = Field(default=None)
    email : Optional[str] = Field(default=None)
    phone : Optional[str] = Field(default=None)

class ChangePass(BaseModel):
    current_password : str
    new_password : str

# User authentication function: 
def authenticate_user(username:str, password:str,db):
    user = db.query(Users).filter(Users.username == username).first()
    if user is None:
        return False
    if bcrypt_context.verify(password,user.password):
        return user
    return False





# CREATE TOKEN:
def create_access_token(username:str,user_id:int,role:str,expire_time:timedelta):
    encode = {'sub':username,'id':user_id,'role':role}
    current_time = datetime.now(timezone.utc) + expire_time
    encode.update({'exp':current_time}) 
    return jwt.encode(encode,SECRET_KEY,algorithm=ALGORITHM)


# GET CURRENT USER
def get_current_user(Token : Annotated[str,Depends(Oauth2_bearer)]):
    payload = jwt.decode(Token,SECRET_KEY,algorithms=[ALGORITHM])
    username : str = payload.get('sub')
    user_id : int = payload.get('id')
    role : str = payload.get('role')
    
    if username  is None or user_id is None:
        raise HTTPException(status_code=404,detail='User not found')
    return {'username':username,'user_id':user_id,'role':role}

user_dependency = Annotated[dict,Depends(get_current_user)]

@router.post('/create/user')
def createUser(db : db_dependency, newUser : CreateUser):
    new_user = Users(
        firstname = newUser.firstname,
        lastname = newUser.lastname,
        username = newUser.username,
        email = newUser.email,
        phone = newUser.phone,
        password = bcrypt_context.hash(newUser.password),
        role = newUser.role

    )
    

    db.add(new_user)
    db.commit()
    
    return JSONResponse(status_code=201,content={'message':'User created successfully'})
    

@router.post('/login')
def login(db:db_dependency,form_data:Annotated[OAuth2PasswordRequestForm,Depends()]):
    user = authenticate_user(form_data.username,form_data.password,db)
    
    if not user:
        raise HTTPException(status_code=401,detail='Failed Authentication')
    
    token = create_access_token(user.username,user.id,user.role,timedelta(minutes=60))
    return {'access_token':token, 'token_type':'bearer'}


@router.put('/update/user')
def Update_user(user : user_dependency,db:db_dependency,UpdateUserInfo : UpdateUser):
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')
    
    User = db.query(Users).filter(Users.id == user.get('user_id')).first()
    
    UpdateUser = UpdateUserInfo.model_dump(exclude_unset=True)
    
    for key,value in UpdateUser.items():
        setattr(User,key,value)
        
    db.commit()
    return JSONResponse(status_code=200, content={'message' : 'User updated successfully'})

@router.put('/change/password')
def Change_Password(user : user_dependency, db : db_dependency, newPassword : ChangePass):
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')
    
    User = db.query(Users).filter(Users.id == user.get('user_id')).first()
    
    if bcrypt_context.verify(newPassword.current_password,User.password):
        User.password = bcrypt_context.hash(newPassword.new_password)
        db.commit()
        return JSONResponse(status_code=201,content={'message':'Password changed successfully'})
    raise HTTPException(status_code=400, detail='Incorrect password')