import os
import pandas as pd
from typing import List, Dict, Any, Optional

from app.extraction.extractors import ExtractionCompetition
from app.extraction.scorer import table_scorer
from app.extraction.semantic_parser import semantic_parser
from app.extraction.notes_extractor import extract_notes_from_pdf, load_notes_to_database
from app.database.connection import SessionLocal
from app.database.seed import ensure_magalu_company, ensure_basic_metrics
from app.models import Company, Document, Metric, Scope, FinancialFact, Note


class ExtractionPipeline:
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.competition = ExtractionCompetition()
    
    def run(self) -> Dict[str, Any]:
        """Executa o pipeline completo"""
        print(f"\n📄 Iniciando extração do PDF: {self.pdf_path}")
        
        if not os.path.exists(self.pdf_path):
            return {"success": False, "error": f"PDF não encontrado: {self.pdf_path}"}
        
        # 1. Extração
        extraction_results = self.competition.extract_all(self.pdf_path)
        
        # 2. Coleta tabelas
        all_tables = []
        for extractor_name, tables in extraction_results.items():
            for table in tables:
                if table is not None and not table.empty:
                    all_tables.append(table)
        
        if not all_tables:
            return {"success": False, "error": "Nenhuma tabela encontrada"}
        
        # 3. Seleciona melhor tabela
        best_table = table_scorer.get_best_table(all_tables)
        
        if best_table is None:
            return {"success": False, "error": "Nenhuma tabela válida encontrada"}
        
        print(f"\n📊 Melhor tabela: {best_table.shape[0]} linhas x {best_table.shape[1]} colunas")
        
        # 4. Parsing
        extracted_metrics = semantic_parser.parse_table(best_table)
        print(f"\n📈 Métricas extraídas: {len(extracted_metrics)}")
        
        # 5. Salva no banco
        saved_count = self._save_to_database(extracted_metrics)
        
        # 6. Extrai notas
        notes_count = self._extract_notes()
        
        return {
            "success": True,
            "tables_found": len(all_tables),
            "best_table_shape": [best_table.shape[0], best_table.shape[1]],
            "metrics_extracted": len(extracted_metrics),
            "metrics_saved": saved_count,
            "notes_extracted": notes_count,
            "extracted_metrics": extracted_metrics[:5]
        }
    
    def _save_to_database(self, metrics: List[Dict[str, Any]]) -> int:
        """Salva métricas no banco"""
        db = SessionLocal()
        saved = 0
        
        try:
            company = ensure_magalu_company(db)
            ensure_basic_metrics(db)
            
            # Documento
            doc = db.query(Document).filter(
                Document.company_id == company.id,
                Document.fiscal_year == 2022,
                Document.fiscal_quarter == 1
            ).first()
            
            if not doc:
                from datetime import date
                doc = Document(
                    company_id=company.id,
                    document_type="ITR",
                    fiscal_year=2022,
                    fiscal_quarter=1,
                    period_end=date(2022, 3, 31),
                    file_reference=os.path.basename(self.pdf_path)
                )
                db.add(doc)
                db.flush()
            
            # Escopo
            scope = db.query(Scope).filter(Scope.name == "Consolidado").first()
            if not scope:
                scope = Scope(name="Consolidado")
                db.add(scope)
                db.flush()
            
            for metric_data in metrics:
                metric = db.query(Metric).filter(Metric.name == metric_data["metric_name"]).first()
                if not metric:
                    metric = Metric(
                        name=metric_data["metric_name"],
                        display_name=metric_data["metric_name"],
                        category="Extraído"
                    )
                    db.add(metric)
                    db.flush()
                
                existing = db.query(FinancialFact).filter(
                    FinancialFact.company_id == company.id,
                    FinancialFact.document_id == doc.id,
                    FinancialFact.metric_id == metric.id,
                    FinancialFact.scope_id == scope.id
                ).first()
                
                if not existing:
                    fact = FinancialFact(
                        company_id=company.id,
                        document_id=doc.id,
                        metric_id=metric.id,
                        scope_id=scope.id,
                        value=metric_data["value"],
                        page=metric_data.get("page", 0),
                        note_reference="Extraído do PDF"
                    )
                    db.add(fact)
                    saved += 1
            
            db.commit()
            print(f"\n💾 Salvo: {saved} novos fatos")
            
        except Exception as e:
            print(f"Erro: {e}")
            db.rollback()
        finally:
            db.close()
        
        return saved
    
    def _extract_notes(self) -> int:
        """Extrai notas explicativas"""
        db = SessionLocal()
        try:
            doc = db.query(Document).filter(
                Document.fiscal_year == 2022,
                Document.fiscal_quarter == 1
            ).first()
            
            if not doc:
                return 0
            
            return load_notes_to_database(self.pdf_path, doc.id)
            
        except Exception as e:
            print(f"Erro nas notas: {e}")
            return 0
        finally:
            db.close()