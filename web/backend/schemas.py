from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CustomerBase(BaseModel):
    name: str
    phone: str
    status: Optional[str] = "待跟进"
    tags: Optional[str] = ""
    remark: Optional[str] = ""

class CustomerCreate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

class CallRecordResponse(BaseModel):
    id: int
    audio_path: str
    duration: int
    intent_level: str
    summary: str
    created_at: datetime
    
    class Config:
        orm_mode = True

class CustomerDetailResponse(CustomerResponse):
    calls: List[CallRecordResponse] = []
