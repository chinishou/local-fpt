"""
SQLAlchemy models for LocalFPT - Synchronous.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime


Base = declarative_base()


class EntityRecord(Base):
    __tablename__ = 'entity_records'

    id = Column(Integer, primary_key=True)
    entity_type = Column(String(64), nullable=False, index=True)
    retired = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    field_values = relationship("FieldValue", back_populates="record", cascade="all, delete-orphan")

    def to_dict(self, fields=None):
        result = {'type': self.entity_type, 'id': self.id}
        for fv in self.field_values:
            if fields is None or fv.field_name in fields:
                result[fv.field_name] = fv.value
        return result


class FieldValue(Base):
    __tablename__ = 'field_values'

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(Integer, ForeignKey('entity_records.id', ondelete='CASCADE'), nullable=False, index=True)
    field_name = Column(String(64), nullable=False, index=True)
    value = Column(JSON, nullable=True)

    record = relationship("EntityRecord", back_populates="field_values")


class EntityMeta(Base):
    __tablename__ = 'entity_meta'

    id = Column(Integer, primary_key=True)
    entity_type = Column(String(64), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class FieldMeta(Base):
    __tablename__ = 'field_meta'

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(64), nullable=False)
    field_name = Column(String(64), nullable=False)
    data_type = Column(String(32), nullable=False)
    properties = Column(JSON, default=dict)


class EventLogEntry(Base):
    __tablename__ = 'event_log_entries'

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(64), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False, index=True)
    event_type = Column(String(32), nullable=False)
    attribute_name = Column(String(64), nullable=True)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(Integer, nullable=True)
