# app/schemas/swimmer.py
from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional
from enum import Enum


class SwimmerStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    DELETED = "DELETED"


class SwimmerGenderEnum(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class SwimmerProfileEnum(str, Enum):
    COMPETITIVE = "COMPETITIVE"
    FORMATIVE = "FORMATIVE"


class SwimmerBase(BaseModel):
    first_name_1: str
    first_name_2: Optional[str] = None
    last_name_1: str
    last_name_2: Optional[str] = None
    birth_date: Optional[date] = None
    document_id: Optional[str] = None
    gender: Optional[SwimmerGenderEnum] = None
    comuna: Optional[str] = None
    institution: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    profile: Optional[SwimmerProfileEnum] = None          
    is_federated: Optional[bool] = None                    


class SwimmerCreate(SwimmerBase):
    pass


class SwimmerUpdate(BaseModel):
    first_name_1: Optional[str] = None
    first_name_2: Optional[str] = None
    last_name_1: Optional[str] = None
    last_name_2: Optional[str] = None
    birth_date: Optional[date] = None
    document_id: Optional[str] = None
    gender: Optional[SwimmerGenderEnum] = None
    comuna: Optional[str] = None
    institution: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    profile: Optional[SwimmerProfileEnum] = None            
    is_federated: Optional[bool] = None                     


class SwimmerStatusUpdate(BaseModel):
    status: SwimmerStatusEnum
    reason: Optional[str] = None


class SwimmerOut(SwimmerBase):  
    model_config = ConfigDict(from_attributes=True)
    id: int
    category: Optional[str] = None
    status: SwimmerStatusEnum
    status_reason: Optional[str] = None
    created_at: datetime