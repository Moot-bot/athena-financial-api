from sqlalchemy.orm import Session
from datetime import date
from app.database.connection import SessionLocal
from app.models import Company, Document, Metric, Scope, FinancialFact

def seed_data(session: Session):
    """Insere dados iniciais baseados no ITR Magazine Luiza 1T22"""
    
    # Verifica se já existem dados
    if session.query(Company).first():
        print("Dados já existem. Pulando seed.")
        return
    
    print("Inserindo dados iniciais...")
    
    # 1. Empresa
    magalu = Company(
        name="Magazine Luiza",
        ticker="MGLU3",
        cnpj="47.960.950/0001-87"
    )
    session.add(magalu)
    session.flush()
    
    # 2. Documento
    doc = Document(
        company_id=magalu.id,
        document_type="ITR",
        fiscal_year=2022,
        fiscal_quarter=1,
        period_end=date(2022, 3, 31),
        filing_date=date(2022, 5, 15),
        file_reference="magalu_itr_1t22.pdf"
    )
    session.add(doc)
    session.flush()
    
    # 3. Escopos
    consolidado = Scope(name="Consolidado", description="Valores consolidados do grupo")
    controladora = Scope(name="Controladora", description="Apenas a empresa controladora")
    session.add_all([consolidado, controladora])
    session.flush()
    
    # 4. Métricas (com hierarquia)
    metrics_data = [
        # Receitas
        ("Receita líquida de vendas", "Receita Líquida", "Receita", "DRE"),
        ("Lucro bruto", "Lucro Bruto", "Resultado", "DRE"),
        ("Lucro líquido do período", "Lucro Líquido", "Resultado", "DRE"),
        
        # Passivo
        ("Empréstimos e financiamentos", "Dívida Total", "Passivo", "BP"),
        ("Patrimônio líquido", "Patrimônio Líquido", "PL", "BP"),
        
        # Ativo
        ("Ativo total", "Ativo Total", "Ativo", "BP"),
        ("Ativo circulante", "Ativo Circulante", "Ativo", "BP"),
        ("Disponibilidades", "Caixa e Equivalentes", "Ativo", "BP"),
        
        # Fluxo de Caixa
        ("Fluxo de caixa operacional", "FCO", "Fluxo", "DFC"),
        ("Fluxo de caixa de investimento", "FCI", "Fluxo", "DFC"),
        ("Fluxo de caixa de financiamento", "FCF", "Fluxo", "DFC"),
    ]
    
    metrics = {}
    for name, display_name, category, statement in metrics_data:
        metric = Metric(
            name=name,
            display_name=display_name,
            category=category,
            statement=statement
        )
        session.add(metric)
        metrics[name] = metric
    
    session.flush()
    
    # 5. Fatos financeiros
    facts_data = [
        # DRE - página 7
        (magalu.id, doc.id, metrics["Receita líquida de vendas"].id, consolidado.id, 8762176, 7, "24"),
        (magalu.id, doc.id, metrics["Lucro bruto"].id, consolidado.id, 2870000, 7, "24"),
        (magalu.id, doc.id, metrics["Lucro líquido do período"].id, consolidado.id, 118000, 7, "24"),
        
        # BP - páginas 5-6
        (magalu.id, doc.id, metrics["Empréstimos e financiamentos"].id, consolidado.id, 4022000, 30, "19"),
        (magalu.id, doc.id, metrics["Patrimônio líquido"].id, consolidado.id, 5000000, 6, "19"),
        (magalu.id, doc.id, metrics["Ativo total"].id, consolidado.id, 39250000, 5, None),
        (magalu.id, doc.id, metrics["Ativo circulante"].id, consolidado.id, 21800000, 5, None),
        (magalu.id, doc.id, metrics["Disponibilidades"].id, consolidado.id, 4250000, 5, "5"),
        
        # DFC - página 10
        (magalu.id, doc.id, metrics["Fluxo de caixa operacional"].id, consolidado.id, 1250000, 10, None),
        (magalu.id, doc.id, metrics["Fluxo de caixa de investimento"].id, consolidado.id, -980000, 10, None),
        (magalu.id, doc.id, metrics["Fluxo de caixa de financiamento"].id, consolidado.id, -210000, 10, None),
    ]
    
    for fact_data in facts_data:
        fact = FinancialFact(
            company_id=fact_data[0],
            document_id=fact_data[1],
            metric_id=fact_data[2],
            scope_id=fact_data[3],
            value=fact_data[4],
            page=fact_data[5],
            note_reference=fact_data[6]
        )
        session.add(fact)
    
    session.commit()
    print(f"Seed concluído: {len(metrics)} métricas, {len(facts_data)} fatos inseridos.")


def run_seed():
    """Função principal para executar o seed"""
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()