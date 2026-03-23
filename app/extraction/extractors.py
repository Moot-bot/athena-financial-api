import pdfplumber
import tabula
import camelot
import pandas as pd
from typing import List, Dict, Any, Optional
import re

class PDFExtractor:
    """Classe base para extratores"""
    
    def extract(self, pdf_path: str) -> List[pd.DataFrame]:
        raise NotImplementedError
    
    @property
    def name(self) -> str:
        return self.__class__.__name__


class PdfPlumberExtractor(PDFExtractor):
    """Extrator usando pdfplumber"""
    
    def extract(self, pdf_path: str) -> List[pd.DataFrame]:
        tables = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    extracted = page.extract_tables()
                    for table in extracted:
                        if table and len(table) > 1:
                            df = pd.DataFrame(table)
                            df['_page'] = page_num
                            tables.append(df)
        except Exception as e:
            print(f"pdfplumber error: {e}")
        return tables


class TabulaExtractor(PDFExtractor):
    """Extrator usando tabula-java"""
    
    def extract(self, pdf_path: str) -> List[pd.DataFrame]:
        tables = []
        try:
            extracted = tabula.read_pdf(
                pdf_path,
                pages='all',
                multiple_tables=True,
                pandas_options={'header': None}
            )
            for i, df in enumerate(extracted):
                if df is not None and not df.empty:
                    tables.append(df)
        except Exception as e:
            print(f"tabula error: {e}")
        return tables


class CamelotExtractor(PDFExtractor):
    """Extrator usando camelot"""
    
    def extract(self, pdf_path: str) -> List[pd.DataFrame]:
        tables = []
        try:
            extracted = camelot.read_pdf(pdf_path, pages='all', flavor='lattice')
            for table in extracted:
                df = table.df
                if not df.empty:
                    tables.append(df)
        except Exception as e:
            print(f"camelot error: {e}")
        return tables


class TableScorer:
    """Avalia a qualidade de uma tabela extraída"""
    
    # Palavras-chave que indicam demonstrações financeiras
    FINANCIAL_KEYWORDS = [
        "receita", "lucro", "caixa", "ativo", "passivo", "patrimônio",
        "resultado", "despesa", "custo", "estoque", "divida", "empréstimo",
        "balanço", "dre", "dfc", "fluxo"
    ]
    
    def score(self, df: pd.DataFrame) -> float:
        """Calcula score de qualidade da tabela"""
        score = 0.0
        
        if df is None or df.empty:
            return 0.0
        
        # Converte para string para análise
        df_str = df.astype(str)
        text = " ".join(df_str.values.flatten()).lower()
        
        # 1. Presença de palavras-chave financeiras (max 30 pts)
        keyword_score = 0
        for kw in self.FINANCIAL_KEYWORDS:
            if kw in text:
                keyword_score += 3
        score += min(keyword_score, 30)
        
        # 2. Densidade numérica (max 30 pts)
        numeric_count = 0
        total = df.size
        
        for val in df.values.flatten():
            if re.search(r'\d', str(val)):
                numeric_count += 1
        
        density = numeric_count / total if total > 0 else 0
        score += density * 30
        
        # 3. Estrutura: pelo menos 3 colunas (10 pts)
        if df.shape[1] >= 3:
            score += 10
        
        # 4. Linhas com texto + número (max 20 pts)
        mixed_rows = 0
        for _, row in df.iterrows():
            row_text = " ".join(str(x) for x in row)
            has_text = bool(re.search(r'[a-zA-Z]', row_text))
            has_number = bool(re.search(r'\d', row_text))
            if has_text and has_number:
                mixed_rows += 1
        
        score += min(mixed_rows, 20)
        
        # 5. Bônus: parece ser demonstração financeira (10 pts)
        if "receita" in text and ("lucro" in text or "resultado" in text):
            score += 10
        
        return score


class ExtractionCompetition:
    """Gerencia a competição entre extratores"""
    
    def __init__(self):
        self.extractors = [
            PdfPlumberExtractor(),
            TabulaExtractor(),
            CamelotExtractor()
        ]
        self.scorer = TableScorer()
    
    def extract_all(self, pdf_path: str) -> Dict[str, List[pd.DataFrame]]:
        """Executa todos os extratores"""
        results = {}
        for extractor in self.extractors:
            try:
                tables = extractor.extract(pdf_path)
                results[extractor.name] = tables
                print(f"{extractor.name}: {len(tables)} tabelas extraídas")
            except Exception as e:
                print(f"{extractor.name} falhou: {e}")
                results[extractor.name] = []
        return results
    
    def select_best_table(self, extraction_results: Dict[str, List[pd.DataFrame]]) -> Optional[pd.DataFrame]:
        """Seleciona a melhor tabela entre todos os extratores"""
        best_score = -1
        best_table = None
        best_source = None
        
        for extractor_name, tables in extraction_results.items():
            for table in tables:
                if table is None or table.empty:
                    continue
                
                score = self.scorer.score(table)
                if score > best_score:
                    best_score = score
                    best_table = table
                    best_source = extractor_name
        
        if best_table is not None:
            print(f"\n✅ Melhor tabela: {best_source} (score: {best_score:.2f})")
        
        return best_table