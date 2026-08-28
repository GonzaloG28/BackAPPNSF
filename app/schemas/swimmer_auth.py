from pydantic import BaseModel

class SwimmerLoginRequest(BaseModel):
    username: str
    password: str

class SwimmerLoginResponse(BaseModel):
    access_token: str
    must_change_password: bool

class SwimmerChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str