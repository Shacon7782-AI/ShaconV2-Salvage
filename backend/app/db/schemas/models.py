from sqlalchemy import Column, Integer, String, JSON, DateTime, func
from pgvector.sqlalchemy import Vector
from .session import Base

class SovereignMemoryNode(Base):
    __tablename__ = "sovereign_memory_nodes"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    metadata_json = Column(JSON, default={})
    # SentenceTransformers 'all-MiniLM-L6-v2' has 384 dimensions
    embedding = Column(Vector(384))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ResearchKnowledge(Base):
    __tablename__ = "research_knowledge"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, index=True)
    title = Column(String)
    url = Column(String)
    url_hash = Column(String, index=True)
    snippet = Column(String)
    source = Column(String)
    query_type = Column(String) # code, news, research, etc.
    score = Column(String) # Store as string for flexibility
    created_at = Column(DateTime(timezone=True), server_default=func.now())
