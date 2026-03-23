from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import Optional
import os

from app.config import API_HOST, API_PORT, API_DEBUG, TEMPLATES_DIR, STATIC_DIR, PDF_PATH
from app.database.connection import get_db, init_db
from app.database.seed import run_seed
from app.database.queries import (
    query_financial_data,
    query_metrics_for_period,
    query_time_series,
    get_companies,
    get_available_periods,
    search_by_metric_name
)
from app.parser.question_parser import parser
from app.rag.retriever import note_retriever
from app.extraction.pipeline import ExtractionPipeline
from app.schemas.responses import QueryResponse, SourceInfo, ErrorResponse, HealthResponse

import os

# Inicialização
init_db()
run_seed()

# Criação da app
app = FastAPI(
    title="Athena Financial Data API",
    description="API para consulta de dados financeiros estruturados",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates e arquivos estáticos
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ==================== FRONTEND ====================

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Página principal"""
    return templates.TemplateResponse("index.html", {"request": request})


# ==================== API ENDPOINTS ====================

@app.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """Verifica o status da API"""
    try:
        db.execute("SELECT 1")
        return HealthResponse(
            status="healthy",
            database="connected"
        )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": str(e)}
        )


@app.get("/query", response_model=QueryResponse)
def query(question: str, db: Session = Depends(get_db)):
    """Consulta em linguagem natural"""
    parsed = parser.parse(question)
    
    is_valid, error_msg = parser.validate(parsed)
    if not is_valid:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(error=error_msg, parsed_query=parsed).dict()
        )
    
    result = query_financial_data(
        session=db,
        metric_name=parsed["metric"],
        company_name=parsed["company"],
        year=parsed["year"],
        quarter=parsed["quarter"],
        scope_name=parsed["scope"]
    )
    
    if not result:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="Dados não encontrados",
                parsed_query=parsed
            ).dict()
        )
    
    fact, metric, doc, company, scope = result
    
    valor_formatado = f"R$ {fact.value:,.0f}".replace(",", ".")
    
    answer = (
        f"A {metric.display_name or metric.name} da {company.name} "
        f"no {doc.period_display} ({scope.name}) "
        f"foi de {valor_formatado}."
    )
    
    source = SourceInfo(
        document=f"{doc.document_type} {doc.fiscal_year}",
        page=fact.page,
        note=fact.note_reference,
        quarter=doc.period_display,
        scope=scope.name
    )
    
    return QueryResponse(
        question=question,
        answer=answer,
        source=source,
        parsed_query=parsed
    )


@app.post("/extract")
def extract_pdf():
    """Executa extração do PDF"""
    if not os.path.exists(PDF_PATH):
        return {"error": f"PDF não encontrado em {PDF_PATH}"}
    
    pipeline = ExtractionPipeline(PDF_PATH)
    result = pipeline.run()
    return result


@app.get("/rag")
def rag_query(question: str, db: Session = Depends(get_db)):
    """Consulta RAG com Grok"""
    # Primeiro tenta dados estruturados
    parsed = parser.parse(question)
    
    if parsed["metric"] and parsed["year"]:
        result = query_financial_data(
            session=db,
            metric_name=parsed["metric"],
            company_name=parsed["company"] or "Magazine Luiza",
            year=parsed["year"],
            quarter=parsed["quarter"],
            scope_name=parsed["scope"]
        )
        
        if result:
            fact, metric, doc, company, scope = result
            return {
                "type": "structured",
                "answer": f"A {metric.name} foi de R$ {fact.value:,.0f}",
                "source": {
                    "page": fact.page,
                    "note": fact.note_reference,
                    "document": f"{doc.document_type} {doc.fiscal_year}"
                }
            }
    
    # RAG para notas
    rag_result = note_retriever.retrieve_and_answer(question)
    return {
        "type": "rag",
        **rag_result,
        "model": "grok-beta"
    }


@app.get("/metrics/search")
def search_metrics(q: str = "", limit: int = 20, db: Session = Depends(get_db)):
    """Busca métricas"""
    results = search_by_metric_name(db, q, limit)
    return [
        {
            "name": m.name,
            "display_name": m.display_name or m.name,
            "category": m.category,
            "statement": m.statement
        }
        for m in results
    ]


@app.get("/companies")
def list_companies(db: Session = Depends(get_db)):
    """Lista empresas"""
    companies = get_companies(db)
    return [{"id": c.id, "name": c.name, "ticker": c.ticker} for c in companies]


@app.get("/periods/{company}")
def get_periods(company: str, db: Session = Depends(get_db)):
    """Lista períodos"""
    periods = get_available_periods(db, company)
    return periods


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=API_DEBUG
    )