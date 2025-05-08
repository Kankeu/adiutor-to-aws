import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text

from .database import Base

class WebPage(Base):
    __tablename__ = 'web_pages'

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String, index=True)
    url = Column(String, unique=True, index=True)
    title = Column(String)
    html = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.UTC))
    updated_at = Column(DateTime, default=datetime.datetime.now(datetime.UTC), onupdate=lambda: datetime.datetime.now(datetime.UTC))