from sqlalchemy import create_engine, Column, String, Integer, Float, ForeignKey, Date, DateTime, Text, Index
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())


class Company(Base):
    """Tabela de empresas"""
    __tablename__ = "companies"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False, unique=True)
    ticker = Column(String(20), nullable=True)
    cnpj = Column(String(18), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    documents = relationship("Document", back_populates="company")
    financial_facts = relationship("FinancialFact", back_populates="company")
    
    def __repr__(self):
        return f"<Company(name='{self.name}')>"


class Document(Base):
    """Tabela de documentos fonte (ITR, DFP, etc.)"""
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    document_type = Column(String(20), nullable=False)  # ITR, DFP, PCA
    fiscal_year = Column(Integer, nullable=False)
    fiscal_quarter = Column(Integer, nullable=True)    # NULL para anual
    period_end = Column(Date, nullable=True)
    filing_date = Column(Date, nullable=True)
    file_reference = Column(String(200), nullable=True)  # caminho do PDF original
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="documents")
    financial_facts = relationship("FinancialFact", back_populates="document")
    
    __table_args__ = (
        Index('idx_document_company_period', 'company_id', 'fiscal_year', 'fiscal_quarter'),
    )
    
    @property
    def period_display(self):
        if self.fiscal_quarter:
            return f"{self.fiscal_quarter}T{str(self.fiscal_year)[-2:]}"
        return str(self.fiscal_year)
    
    def __repr__(self):
        return f"<Document(company='{self.company.name}', period='{self.period_display}')>"


class Metric(Base):
    """Tabela de métricas financeiras (hierárquica)"""
    __tablename__ = "metrics"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False, unique=True)
    display_name = Column(String(200), nullable=True)
    parent_id = Column(String(36), ForeignKey("metrics.id"), nullable=True)
    category = Column(String(50), nullable=True)  # Receita, Despesa, Ativo, Passivo, PL, Fluxo
    statement = Column(String(50), nullable=True)  # BP, DRE, DFC, DVA, Nota
    unit = Column(String(20), default="R$ mil")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    children = relationship("Metric", backref="parent", remote_side=[id])
    financial_facts = relationship("FinancialFact", back_populates="metric")
    
    def __repr__(self):
        return f"<Metric(name='{self.name}')>"


class Scope(Base):
    """Tabela de escopo (Controladora / Consolidado)"""
    __tablename__ = "scopes"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(200), nullable=True)
    
    # Relationships
    financial_facts = relationship("FinancialFact", back_populates="scope")
    
    def __repr__(self):
        return f"<Scope(name='{self.name}')>"


class FinancialFact(Base):
    """Tabela fato - valores financeiros com rastreabilidade"""
    __tablename__ = "financial_facts"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    metric_id = Column(String(36), ForeignKey("metrics.id"), nullable=False)
    scope_id = Column(String(36), ForeignKey("scopes.id"), nullable=False)
    
    value = Column(Float, nullable=False)
    
    # Rastreabilidade
    page = Column(Integer, nullable=True)
    note_reference = Column(String(50), nullable=True)
    table_reference = Column(String(100), nullable=True)
    line_number = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="financial_facts")
    document = relationship("Document", back_populates="financial_facts")
    metric = relationship("Metric", back_populates="financial_facts")
    scope = relationship("Scope", back_populates="financial_facts")
    
    __table_args__ = (
        Index('idx_fact_company_metric_period', 'company_id', 'metric_id', 'document_id'),
        Index('idx_fact_scope', 'scope_id'),
    )
    
    def __repr__(self):
        return f"<FinancialFact(metric='{self.metric.name}', value={self.value})>"


class Note(Base):
    """Tabela para notas explicativas (suporte a RAG)"""
    __tablename__ = "notes"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    note_number = Column(String(20), nullable=False)  # Nota 19, Nota 24, etc.
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    page_start = Column(Integer, nullable=True)
    page_end = Column(Integer, nullable=True)
    embedding = Column(Text, nullable=True)  # Armazenamento do embedding (JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document")
    
    __table_args__ = (
        Index('idx_note_document', 'document_id'),
        Index('idx_note_number', 'note_number'),
    )