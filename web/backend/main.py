from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from .database import engine, Base, get_db
from . import models, schemas

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Autoiphone AI CRM", version="1.0.0")

# 配置 CORS，允许 Vue 前端 (默认 5173 端口) 跨域调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发阶段允许全部
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Autoiphone API is running"}

# ======== 客户模块 ========
@app.post("/api/customers/", response_model=schemas.CustomerResponse)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    db_cust = db.query(models.Customer).filter(models.Customer.phone == customer.phone).first()
    if db_cust:
        raise HTTPException(status_code=400, detail="该号码已存在")
    
    new_cust = models.Customer(**customer.dict())
    db.add(new_cust)
    db.commit()
    db.refresh(new_cust)
    return new_cust

@app.get("/api/customers/", response_model=List[schemas.CustomerResponse])
def get_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    customers = db.query(models.Customer).offset(skip).limit(limit).all()
    return customers

@app.get("/api/customers/{customer_id}", response_model=schemas.CustomerDetailResponse)
def get_customer_detail(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    return customer
