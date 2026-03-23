import re
import pandas as pd
from typing import List, Dict, Any, Optional

class SemanticFinancialParser:
    """
    Extrai métricas financeiras de uma tabela de forma semântica.
    """
    
    METRIC_PATTERNS = {
        "Receita líquida de vendas": [
            r"receita\s+líquida",
            r"receita\s+de\s+vendas",
            r"vendas\s+líquidas",
        ],
        "Lucro bruto": [
            r"lucro\s+bruto",
            r"resultado\s+bruto"
        ],
        "Lucro líquido do período": [
            r"lucro\s+líquido",
            r"resultado\s+líquido",
        ],
        "Empréstimos e financiamentos": [
            r"empréstimos\s+e\s+financiamentos",
            r"dívida\s+total",
        ],
        "Patrimônio líquido": [
            r"patrimônio\s+líquido",
            r"patrimonio\s+líquido",
        ],
        "Ativo total": [
            r"ativo\s+total",
        ],
    }
    
    def __init__(self):
        self.compiled_patterns = {}
        for metric, patterns in self.METRIC_PATTERNS.items():
            self.compiled_patterns[metric] = [re.compile(p, re.IGNORECASE) for p in patterns]
    
    def parse_table(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Extrai métricas da tabela"""
        results = []
        
        if df is None or df.empty:
            return results
        
        numeric_cols = self._find_numeric_columns(df)
        if not numeric_cols:
            return results
        
        for idx, row in df.iterrows():
            row_text = " ".join(str(x).lower() for x in row.values)
            metric_name = self._identify_metric(row_text)
            
            if metric_name:
                value = self._extract_value(row, numeric_cols)
                if value is not None:
                    results.append({
                        "metric_name": metric_name,
                        "value": value,
                        "page": self._extract_page(row, df),
                        "row_index": idx
                    })
        
        return results
    
    def _find_numeric_columns(self, df: pd.DataFrame) -> List[int]:
        """Identifica colunas numéricas"""
        numeric_cols = []
        for col in range(df.shape[1]):
            col_values = df.iloc[:, col].astype(str)
            numeric_count = sum(1 for v in col_values if self._looks_like_number(v))
            if numeric_count > len(col_values) * 0.3:
                numeric_cols.append(col)
        return numeric_cols
    
    def _looks_like_number(self, value: str) -> bool:
        """Verifica se parece número"""
        if not value or not value.strip():
            return False
        cleaned = re.sub(r'[R$\s\(\)]', '', str(value))
        cleaned = cleaned.replace('.', '').replace(',', '.').strip()
        try:
            float(cleaned)
            return True
        except:
            return False
    
    def _identify_metric(self, text: str) -> Optional[str]:
        """Identifica métrica"""
        for metric_name, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    return metric_name
        return None
    
    def _extract_value(self, row: pd.Series, numeric_cols: List[int]) -> Optional[float]:
        """Extrai valor numérico"""
        for col in numeric_cols:
            val = row.iloc[col]
            if pd.isna(val):
                continue
            
            val_str = str(val).strip()
            if not val_str:
                continue
            
            negative = '(' in val_str and ')' in val_str
            cleaned = re.sub(r'[R$\s\(\)]', '', val_str)
            cleaned = cleaned.replace('.', '').replace(',', '.')
            
            match = re.search(r'(-?\d+(?:\.\d+)?)', cleaned)
            if match:
                try:
                    value = float(match.group(1))
                    if negative:
                        value = -value
                    return value
                except:
                    pass
        return None
    
    def _extract_page(self, row: pd.Series, df: pd.DataFrame) -> Optional[int]:
        """Extrai página"""
        if '_page' in df.columns:
            return row.get('_page')
        return None


semantic_parser = SemanticFinancialParser()