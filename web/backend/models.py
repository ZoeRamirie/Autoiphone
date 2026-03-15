from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    phone = Column(String, unique=True, index=True)
    status = Column(String, default="待跟进")  # 待跟进, 高意向, 拒绝, 无效号码等
    tags = Column(String, default="")  # 使用逗号分隔的标签序列
    remark = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联通话记录
    calls = relationship("CallRecord", back_populates="customer")

class CallRecord(Base):
    __tablename__ = "call_records"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    audio_path = Column(String, default="")  # 录音文件在服务器上的相对路径
    transcript = Column(JSON, default=list)  # 保存完整的通话对白 JSON
    duration = Column(Integer, default=0)    # 通话时长 (秒)
    intent_level = Column(String, default="未知") # AI 总结的意向度评级
    summary = Column(Text, default="")       # AI 提取的通话总结
    created_at = Column(DateTime, default=datetime.utcnow)
    
    customer = relationship("Customer", back_populates="calls")

class VoiceTemplate(Base):
    """保存每个销售人员录制的声音克隆模板 ID"""
    __tablename__ = "voice_templates"

    id = Column(Integer, primary_key=True, index=True)
    employee_name = Column(String, unique=True, index=True)
    voice_id = Column(String)  # 阿里云 CosyVoice ID
    sample_text = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
