from datetime import date
from enum import Enum
from typing import Union, List, Dict

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.encoders import jsonable_encoder
from fastapi_login.exceptions import InvalidCredentialsException
import hashlib
from pydantic import BaseModel, AnyUrl

from settings import manager, deta

class ResponseFormat(BaseModel):
    status: int
    success: bool
    message: str
    data: Union[Dict, List]

class ActType(str, Enum):
    edu = 'edu'
    work = 'work'

class Link(BaseModel):
    github: AnyUrl
    demo: AnyUrl

class Contact(BaseModel):
    username: str
    name: str
    label: str
    link: Union[AnyUrl, None] = None

class Project(BaseModel):
    username: str
    title: str
    date: str
    summary: str
    image: str
    stack: List[str]
    link: Link

class Timeline(BaseModel):
    username: str
    title: str
    description: str
    place: str
    startDate: Union[str, None] = None
    endDate: Union[str, None] = None
    date: Union[str, None] = None
    act_type: ActType



db_user = deta.Base('portfolio')
db_contact = deta.Base('contact')
db_project = deta.Base('project')
db_timeline = deta.Base('timeline')


description = """
PortfolioAPI adalah tempat anda menyimpan informasi yang biasa ada pada sebuah portfolio seperti kontak, project, dan pengalaman.
## Mendaftar
Untuk bisa menggunakan API ini anda tinggal mendaftar di link signup yang tersedia di bawah dan login dengan cara mengeklik button Authorize di bagian kanan.  
URL yang bisa diakses tanpa login adalah URL dengan method get. Untuk mendapatkan data user harus mendambahkan username pada path parameter get
"""


app = FastAPI(
    title='Portfolio Control',
    description=description,
    version='1.0.0',
)


@manager.user_loader()
def get_user(username: str):
    res = db_user.fetch({'username': username})
    try:
        return res.items[0]
    except:
        return False

@app.get('/')
async def redirect():
    return RedirectResponse('docs')

@app.post('/signup')
async def signup(username: str, password: str):
    user = get_user(username)
    password = hashlib.md5(password.encode('utf-8')).hexdigest()
    
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='User Already Exist'
        )
    
    db_user.put({'username': username, 'password': password})
    return {'success': f"{username} saved"}


@app.post('/login')
async def login(data: OAuth2PasswordRequestForm = Depends()):
    username = data.username
    password = data.password
    
    user = get_user(username)
    password = hashlib.md5(password.encode('utf-8')).hexdigest()
    
    if not user:
        raise InvalidCredentialsException
    elif password != user['password']:
        raise InvalidCredentialsException
    
    access_token = manager.create_access_token(
        data={'sub': username}
    )
    
    return {'access_token': access_token}


@app.get('/contact/{username}', response_model=ResponseFormat, tags=['contact'])
async def get_contact(username: str):
    res = db_contact.fetch({'username': username})
    return {
        'status': status.HTTP_200_OK,
        'success': True,
        'message': 'Fetch contact success',
        'data': res.items
    }

@app.post('/contact', response_model=ResponseFormat, tags=['contact'])
async def add_contact(name: str, label: str, link: Union[AnyUrl, str], user = Depends(manager)):
    data = {
        'username': user['username'],
        'name': name,
        'label': label,
        'link': link
    }
    db_contact.put(data)
    return {
        'status': status.HTTP_200_OK,
        'success': True,
        'message': 'Fetch contact success',
        'data': data
    }

@app.delete('/contact', response_model=ResponseFormat, tags=['contact'])
async def delete_contact(key: str, user = Depends(manager)):
    res = db_contact.get(key)
    if res['username'] != user['username']:
        return {
            'status': status.HTTP_401_UNAUTHORIZED,
            'success': False,
            'message': "Cannot delete another person's contact",
            'data': {}
        }
    
    db_contact.delete(key)
    return {
        'status': status.HTTP_200_OK,
        'success': True,
        'message': 'Delete contact success',
        'data': res
    }

@app.patch('/contact', response_model=ResponseFormat, tags=['contact'])
async def update_contact(key: str, name: str, label: str, link: Union[AnyUrl, str], user = Depends(manager)):
    res = db_contact.get(key)
    if res['username'] != user['username']:
        return {
            'status': status.HTTP_401_UNAUTHORIZED,
            'success': False,
            'message': "Cannot change another person's contact",
            'data': {}
        }
    
    data = {
        'username': user['username'],
        'name': name,
        'label': label,
        'link': link
    }
    db_contact.update(data, key)
    return {
        'status': status.HTTP_200_OK,
        'success': True,
        'message': 'Update contact success',
        'data': data
    }

@app.get('/project/{username}', response_model=ResponseFormat, tags=['project'])
async def get_project(username: str):
    res = db_project.fetch({'username': username})
    return {
        'status': status.HTTP_200_OK,
        'success': True,
        'message': 'Fetch project success',
        'data': res.items
    }

@app.post('/project', response_model=ResponseFormat, tags=['project'])
async def add_project(title: str,
                      date: str,
                      summary: str,
                      stack: str,
                      github: str,
                      demo: str,
                      image: Union[str, None] = None,
                      user = Depends(manager)):
    data = {
        'username': user['username'],
        'title': title,
        'date': date,
        'summary': summary,
        'stack': stack.replace(' ', '').split(','),
        'github': github,
        'demo': demo,
        'image': image
    }
    db_project.put(jsonable_encoder(data))
    return {
        'status': status.HTTP_200_OK,
        'success': True,
        'message': 'Add project success',
        'data': jsonable_encoder(data)
    }

@app.delete('/project', response_model=ResponseFormat, tags=['project'])
async def delete_project(key: str, user = Depends(manager)):
    res = db_project.get(key)
    if res['username'] != user['username']:
        return {
            'status': status.HTTP_401_UNAUTHORIZED,
            'success': False,
            'message': "Cannot delete another person's project",
            'data': {}
        }
    
    db_project.delete(key)
    return {
        'status': status.HTTP_200_OK,
        'success': True,
        'message': 'Delete project success',
        'data': res
    }

@app.patch('/project', response_model=ResponseFormat, tags=['project'])
async def update_project(key: str,
                         title: str,
                         date: str,
                         summary: str,
                         stack: str,
                         github: str,
                         demo: str,
                         image: Union[str, None] = None,
                         user = Depends(manager)):
    res = db_project.get(key)
    if res['username'] != user['username']:
        return {
            'status': status.HTTP_401_UNAUTHORIZED,
            'success': False,
            'message': "Cannot change another person's project",
            'data': {}
        }
    
    data = {
        'username': user['username'],
        'title': title,
        'date': date,
        'summary': summary,
        'stack': stack.replace(' ', '').split(','),
        'github': github,
        'demo': demo,
        'image': image
    }
    db_project.update(data, key)
    return {
        'status': status.HTTP_200_OK,
        'success': True,
        'message': 'Update project success',
        'data': data
    }

@app.get('/timeline/{username}', response_model=ResponseFormat, tags=['timeline'])
async def get_timeline(username: str):
    res = db_timeline.fetch({'username': username})
    return {
        'status': status.HTTP_200_OK,
        'success': True,
        'message': 'Fetch timeline success',
        'data': res.items
    }

@app.post('/timeline', response_model=ResponseFormat, tags=['timeline'])
async def add_timeline(title: str,
                       description: str,
                       place: str,
                       acttype: ActType,
                       start_date: Union[str, None] = None,
                       end_date: Union[str, None] = None,
                       date_: Union[str, None] = None,
                       user = Depends(manager)):
    data = {
        'username': user['username'],
        'title': title,
        'description': description,
        'place': place,
        'type': acttype,
        'startDate': start_date,
        'endDate': end_date,
        'date': date_,
    }
    db_timeline.put(data)
    
    return {
        'status': status.HTTP_200_OK,
        'success': True,
        'message': 'Add timeline success',
        'data': data
    }

@app.delete('/timeline', response_model=ResponseFormat, tags=['timeline'])
async def delete_timeline(key: str, user = Depends(manager)):
    res = db_timeline.get(key)
    if res['username'] != user['username']:
        return {
            'status': status.HTTP_401_UNAUTHORIZED,
            'success': False,
            'message': "Cannot delete another person's timeline",
            'data': {}
        }
    
    db_timeline.delete(key)
    
    return {
        'status': status.HTTP_200_OK,
        'success': True,
        'message': 'Delete timeline success',
        'data': res
    }


@app.patch('/timeline', response_model=ResponseFormat, tags=['timeline'])
async def update_timeline(key: str,
                          title: str,
                          description: str,
                          place: str,
                          acttype: ActType,
                          start_date: Union[str, None] = None,
                          end_date: Union[str, None] = None,
                          date_: Union[str, None] = None,
                          user = Depends(manager)):
    res = db_timeline.get(key)
    if res['username'] != user['username']:
        return {
            'status': status.HTTP_401_UNAUTHORIZED,
            'success': False,
            'message': "Cannot change another person's timeline",
            'data': {}
        }
    
    data = {
        'username': user['username'],
        'title': title,
        'description': description,
        'place': place,
        'type': acttype,
        'startDate': start_date,
        'endDate': end_date,
        'date': date_,
    }
    db_timeline.update(data, key)
    return {
        'status': status.HTTP_200_OK,
        'success': True,
        'message': 'Update timeline success',
        'data': data
    }

