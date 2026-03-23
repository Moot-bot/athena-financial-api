#!/usr/bin/env python
"""
Script para executar a extração do PDF e carregar no banco
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.extraction.pipeline import ExtractionPipeline
from app.extraction.notes_extractor import load_notes_to_database
from app.database.connection import init_db, SessionLocal
from app.database.seed import ensure_magalu_company, ensure_basic_metrics
from app.models import Document

PDF_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "magazine_luiza_itr_1t22.pdf")

def main():
    print("=" * 60)
    print("🚀 Pipeline de Extração - Magazine Luiza ITR 1T22")
    print("=" * 60)
    
    # 1. Inicializa banco
    print("\n📁 Inicializando banco de dados...")
    init_db()
    
    # 2. Garante empresa e métricas básicas
    db = SessionLocal()
    try:
        company = ensure_magalu_company(db)
        ensure_basic_metrics(db)
        
        # Busca documento
        doc = db.query(Document).filter(
            Document.company_id == company.id,
            Document.fiscal_year == 2022,
            Document.fiscal_quarter == 1
        ).first()
        
        if doc:
            document_id = doc.id
        else:
            # Cria documento
            from datetime import date
            doc = Document(
                company_id=company.id,
                document_type="ITR",
                fiscal_year=2022,
                fiscal_quarter=1,
                period_end=date(2022, 3, 31),
                file_reference=os.path.basename(PDF_PATH)
            )
            db.add(doc)
            db.commit()
            document_id = doc.id
            print(f"✅ Documento criado: {document_id}")
        
    finally:
        db.close()
    
    # 3. Extrai dados financeiros
    print("\n📄 Extraindo dados financeiros do PDF...")
    if os.path.exists(PDF_PATH):
        pipeline = ExtractionPipeline(PDF_PATH)
        result = pipeline.run()
        
        print("\n📊 Resultado da extração:")
        for key, value in result.items():
            if key != "extracted_metrics":
                print(f"   - {key}: {value}")
    else:
        print(f"⚠️ PDF não encontrado em: {PDF_PATH}")
    
    # 4. Extrai notas explicativas
    print("\n📝 Extraindo notas explicativas...")
    if os.path.exists(PDF_PATH):
        db = SessionLocal()
        try:
            doc = db.query(Document).filter(
                Document.fiscal_year == 2022,
                Document.fiscal_quarter == 1
            ).first()
            
            if doc:
                load_notes_to_database(PDF_PATH, doc.id)
        finally:
            db.close()
    
    print("\n✅ Pipeline concluído!")

if __name__ == "__main__":
    main()