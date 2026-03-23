from sqlalchemy.orm import Session
from datetime import date
from app.database.connection import SessionLocal
from app.models import Company, Document, Metric, Scope, FinancialFact

def ensure_magalu_company(db: Session) -> Company:
    """Garante que a empresa Magazine Luiza existe"""
    company = db.query(Company).filter(Company.name == "Magazine Luiza").first()
    if not company:
        company = Company(
            name="Magazine Luiza",
            ticker="MGLU3",
            cnpj="47.960.950/0001-87"
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        print("✅ Empresa Magazine Luiza criada")
    return company

def ensure_basic_metrics(db: Session):
    """Garante que as métricas básicas existem"""
    metrics_data = [
        ("Receita líquida de vendas", "Receita Líquida", "Receita", "DRE"),
        ("Lucro bruto", "Lucro Bruto", "Resultado", "DRE"),
        ("Lucro líquido do período", "Lucro Líquido", "Resultado", "DRE"),
        ("Empréstimos e financiamentos", "Dívida Total", "Passivo", "BP"),
        ("Patrimônio líquido", "Patrimônio Líquido", "PL", "BP"),
        ("Ativo total", "Ativo Total", "Ativo", "BP"),
        ("Ativo circulante", "Ativo Circulante", "Ativo", "BP"),
        ("Disponibilidades", "Caixa e Equivalentes", "Ativo", "BP"),
    ]
    
    for name, display_name, category, statement in metrics_data:
        existing = db.query(Metric).filter(Metric.name == name).first()
        if not existing:
            metric = Metric(
                name=name,
                display_name=display_name,
                category=category,
                statement=statement
            )
            db.add(metric)
    
    db.commit()
    print("✅ Métricas básicas criadas")

def ensure_scopes(db: Session):
    """Garante que os escopos existem"""
    scopes = ["Consolidado", "Controladora"]
    for scope_name in scopes:
        existing = db.query(Scope).filter(Scope.name == scope_name).first()
        if not existing:
            scope = Scope(name=scope_name)
            db.add(scope)
    
    db.commit()
    print("✅ Escopos criados")

def seed_data(db: Session):
    """Insere dados iniciais de exemplo"""
    
    if db.query(FinancialFact).first():
        print("Dados já existem. Pulando seed.")
        return
    
    print("Inserindo dados iniciais...")
    
    company = ensure_magalu_company(db)
    ensure_scopes(db)
    ensure_basic_metrics(db)
    
    consolidado = db.query(Scope).filter(Scope.name == "Consolidado").first()
    
    doc = db.query(Document).filter(
        Document.company_id == company.id,
        Document.fiscal_year == 2022,
        Document.fiscal_quarter == 1
    ).first()
    
    if not doc:
        doc = Document(
            company_id=company.id,
            document_type="ITR",
            fiscal_year=2022,
            fiscal_quarter=1,
            period_end=date(2022, 3, 31),
            file_reference="magazine_luiza_itr_1t22.pdf"
        )
        db.add(doc)
        db.flush()
    
    metrics = {m.name: m for m in db.query(Metric).all()}
    
    facts_data = [
        (metrics.get("Receita líquida de vendas"), 8762176, 7, "24"),
        (metrics.get("Lucro bruto"), 2870000, 7, "24"),
        (metrics.get("Lucro líquido do período"), 118000, 7, "24"),
        (metrics.get("Empréstimos e financiamentos"), 4022000, 30, "19"),
        (metrics.get("Patrimônio líquido"), 5000000, 6, "19"),
        (metrics.get("Ativo total"), 39250000, 5, None),
        (metrics.get("Ativo circulante"), 21800000, 5, None),
        (metrics.get("Disponibilidades"), 4250000, 5, "5"),
    ]
    
    saved = 0
    for metric, value, page, note in facts_data:
        if metric:
            existing = db.query(FinancialFact).filter(
                FinancialFact.company_id == company.id,
                FinancialFact.document_id == doc.id,
                FinancialFact.metric_id == metric.id,
                FinancialFact.scope_id == consolidado.id
            ).first()
            
            if not existing:
                fact = FinancialFact(
                    company_id=company.id,
                    document_id=doc.id,
                    metric_id=metric.id,
                    scope_id=consolidado.id,
                    value=value,
                    page=page,
                    note_reference=note
                )
                db.add(fact)
                saved += 1
    
    db.commit()
    print(f"✅ Seed concluído: {saved} fatos inseridos")

def run_seed():
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()