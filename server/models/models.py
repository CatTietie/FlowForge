from sqlalchemy import Column, Integer, String, JSON, DateTime, Text
from sqlalchemy.sql import func

from database import Base


class FormDefinition(Base):
    __tablename__ = "form_definitions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    schema_json = Column(JSON, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ProcessDefinition(Base):
    __tablename__ = "process_definitions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    definition_json = Column(JSON, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class FormInstance(Base):
    __tablename__ = "form_instances"

    id = Column(Integer, primary_key=True, index=True)
    form_definition_id = Column(Integer, nullable=False)
    data_json = Column(JSON, nullable=False)
    process_instance_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class ProcessInstance(Base):
    __tablename__ = "process_instances"

    id = Column(Integer, primary_key=True, index=True)
    process_definition_id = Column(Integer, nullable=False)
    form_instance_id = Column(Integer, nullable=True)
    current_node_id = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="running")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ApprovalRecord(Base):
    __tablename__ = "approval_records"

    id = Column(Integer, primary_key=True, index=True)
    process_instance_id = Column(Integer, nullable=False)
    node_id = Column(String(100), nullable=False)
    assignee = Column(String(255), nullable=False)
    decision = Column(String(50), nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
