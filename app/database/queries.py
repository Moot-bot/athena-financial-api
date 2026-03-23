from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, List, Dict, Any, Tuple
from app.models import FinancialFact, Metric, Document, Company, Scope
from app.parser.question_parser import parser


def query_financial_data(
    session: Session,
    metric_name: str,
    company_name: str,
    year: int,
    quarter: Optional[int] = None,
    scope_name: str = "Consolidado"
) -> Optional[Tuple[FinancialFact, Metric, Document, Company, Scope]]:
    """
    Consulta um fato financeiro específico.
    
    Returns:
        Tupla (fact, metric, document, company, scope) ou None
    """
    query = session.query(FinancialFact, Metric, Document, Company, Scope)\
        .join(Metric, FinancialFact.metric_id == Metric.id)\
        .join(Document, FinancialFact.document_id == Document.id)\
        .join(Company, FinancialFact.company_id == Company.id)\
        .join(Scope, FinancialFact.scope_id == Scope.id)\
        .filter(
            Metric.name == metric_name,
            Company.name == company_name,
            Document.fiscal_year == year,
            Scope.name == scope_name
        )
    
    if quarter:
        query = query.filter(Document.fiscal_quarter == quarter)
    
    return query.first()


def query_metrics_for_period(
    session: Session,
    company_name: str,
    year: int,
    quarter: Optional[int] = None,
    scope_name: str = "Consolidado"
) -> List[Dict[str, Any]]:
    """
    Retorna todas as métricas disponíveis para um período.
    Útil para contexto e análises exploratórias.
    """
    query = session.query(
        Metric.name,
        Metric.display_name,
        Metric.category,
        FinancialFact.value,
        FinancialFact.page,
        FinancialFact.note_reference,
        Document.fiscal_year,
        Document.fiscal_quarter,
        Scope.name.label("scope")
    ).join(FinancialFact, FinancialFact.metric_id == Metric.id)\
     .join(Document, FinancialFact.document_id == Document.id)\
     .join(Company, FinancialFact.company_id == Company.id)\
     .join(Scope, FinancialFact.scope_id == Scope.id)\
     .filter(
         Company.name == company_name,
         Document.fiscal_year == year,
         Scope.name == scope_name
     )
    
    if quarter:
        query = query.filter(Document.fiscal_quarter == quarter)
    
    results = query.all()
    
    return [
        {
            "metric": r.name,
            "display_name": r.display_name or r.name,
            "category": r.category,
            "value": r.value,
            "source": {
                "page": r.page,
                "note": r.note_reference
            },
            "period": f"{r.fiscal_quarter}T{str(r.fiscal_year)[-2:]}" if r.fiscal_quarter else str(r.fiscal_year)
        }
        for r in results
    ]


def query_time_series(
    session: Session,
    metric_name: str,
    company_name: str,
    years: int = 4,
    scope_name: str = "Consolidado"
) -> List[Dict[str, Any]]:
    """
    Retorna série temporal de uma métrica.
    """
    results = session.query(
        Document.fiscal_year,
        Document.fiscal_quarter,
        FinancialFact.value,
        FinancialFact.page,
        Document.period_end
    ).join(FinancialFact, FinancialFact.document_id == Document.id)\
     .join(Metric, FinancialFact.metric_id == Metric.id)\
     .join(Company, FinancialFact.company_id == Company.id)\
     .join(Scope, FinancialFact.scope_id == Scope.id)\
     .filter(
         Metric.name == metric_name,
         Company.name == company_name,
         Scope.name == scope_name
     )\
     .order_by(desc(Document.fiscal_year), desc(Document.fiscal_quarter))\
     .limit(years * 4)\
     .all()
    
    return [
        {
            "period": f"{r.fiscal_quarter}T{str(r.fiscal_year)[-2:]}" if r.fiscal_quarter else str(r.fiscal_year),
            "value": r.value,
            "source_page": r.page,
            "end_date": r.period_end.isoformat() if r.period_end else None
        }
        for r in results
    ]


def search_by_metric_name(
    session: Session,
    search_term: str,
    limit: int = 10
) -> List[Metric]:
    """
    Busca métricas por nome (para autocomplete).
    """
    return session.query(Metric)\
        .filter(Metric.name.ilike(f"%{search_term}%"))\
        .limit(limit)\
        .all()


def get_companies(session: Session) -> List[Company]:
    """Retorna todas as empresas disponíveis"""
    return session.query(Company).all()


def get_available_periods(
    session: Session,
    company_name: str
) -> List[Dict[str, Any]]:
    """Retorna períodos disponíveis para uma empresa"""
    results = session.query(
        Document.fiscal_year,
        Document.fiscal_quarter,
        Document.period_end
    ).join(Company, Document.company_id == Company.id)\
     .filter(Company.name == company_name)\
     .order_by(desc(Document.fiscal_year), desc(Document.fiscal_quarter))\
     .all()
    
    return [
        {
            "year": r.fiscal_year,
            "quarter": r.fiscal_quarter,
            "period": f"{r.fiscal_quarter}T{str(r.fiscal_year)[-2:]}" if r.fiscal_quarter else str(r.fiscal_year),
            "end_date": r.period_end.isoformat() if r.period_end else None
        }
        for r in results
    ]