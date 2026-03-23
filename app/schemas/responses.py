from pydantic import BaseModel
from typing import Optional, List, Any


class SourceInfo(BaseModel):
    """Informações de rastreabilidade"""
    document: str
    page: Optional[int] = None
    note: Optional[str] = None
    quarter: Optional[str] = None
    scope: str


class QueryResponse(BaseModel):
    """Resposta padrão para consultas"""
    question: str
    answer: str
    source: SourceInfo
    parsed_query: Optional[dict] = None


class MetricInfo(BaseModel):
    """Informação de métrica"""
    metric: str
    display_name: str
    category: Optional[str] = None
    value: float
    source: SourceInfo
    period: str


class TimeSeriesPoint(BaseModel):
    """Ponto de série temporal"""
    period: str
    value: float
    source_page: Optional[int] = None
    end_date: Optional[str] = None


class ErrorResponse(BaseModel):
    """Resposta de erro"""
    error: str
    suggestion: Optional[str] = None
    parsed_query: Optional[dict] = None


class HealthResponse(BaseModel):
    """Resposta de health check"""
    status: str
    database: str
    version: str = "1.0.0"