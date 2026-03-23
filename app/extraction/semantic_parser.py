import re
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple

class SemanticFinancialParser:
    """
    Extrai métricas financeiras de uma tabela de forma semântica.
    """
    
    # Mapeamento de padrões para métricas
    METRIC_PATTERNS = {
        "Receita líquida de vendas": [
            r"receita\s+líquida",
            r"receita\s+de\s+vendas",
            r"vendas\s+líquidas",
            r"receita\s+operacional\s+líquida"
        ],
        "Lucro bruto": [
            r"lucro\s+bruto",
            r"resultado\s+bruto"
        ],
        "Lucro líquido do período": [
            r"lucro\s+líquido",
            r"resultado\s+líquido",
            r"lucro\s+do\s+período",
            r"resultado\s+do\s+período"
        ],
        "Empréstimos e financiamentos": [
            r"empréstimos\s+e\s+financiamentos",
            r"dívida\s+total",
            r"endividamento"
        ],
        "Patrimônio líquido": [
            r"patrimônio\s+líquido",
            r"patrimonio\s+líquido",
            r"pl\s+total"
        ],
        "Ativo total": [
            r"ativo\s+total",
            r"total\s+do\s+ativo"
        ],
        "Ativo circulante": [
            r"ativo\s+circulante",
            r"circulante\s+total"
        ],
        "Disponibilidades": [
            r"disponibilidades",
            r"caixa\s+e\s+equivalentes",
            r"caixa\s+e\s+banco"
        ],
        "Fluxo de caixa operacional": [
            r"fluxo\s+de\s+caixa\s+operacional",
            r"atividades\s+operacionais",
            r"fco"
        ]
    }
    
    def __init__(self):
        self.compiled_patterns = {}
        for metric, patterns in self.METRIC_PATTERNS.items():
            self.compiled_patterns[metric] = [re.compile(p, re.IGNORECASE) for p in patterns]
    
    def parse_table(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Extrai métricas da tabela.
        Retorna lista de dicts com metric_name, value, page, row.
        """
        results = []
        
        # Encontra colunas com valores numéricos
        numeric_cols = self._find_numeric_columns(df)
        
        if not numeric_cols:
            return results
        
        # Processa cada linha
        for idx, row in df.iterrows():
            row_text = " ".join(str(x).lower() for x in row.values)
            
            # Tenta identificar métrica
            metric_name = self._identify_metric(row_text)
            if metric_name:
                # Extrai valor numérico
                value = self._extract_value(row, numeric_cols)
                if value is not None:
                    results.append({
                        "metric_name": metric_name,
                        "value": value,
                        "page": self._extract_page(row, df),
                        "row_index": idx,
                        "row_text": row_text[:100]
                    })
        
        return results
    
    def _find_numeric_columns(self, df: pd.DataFrame) -> List[int]:
        """Identifica colunas que contêm números"""
        numeric_cols = []
        for col in range(df.shape[1]):
            col_values = df.iloc[:, col].astype(str)
            numeric_count = sum(1 for v in col_values if self._looks_like_number(v))
            if numeric_count > len(col_values) * 0.3:
                numeric_cols.append(col)
        return numeric_cols
    
    def _looks_like_number(self, value: str) -> bool:
        """Verifica se valor parece número"""
        if not value or value.strip() == '':
            return False
        # Remove formatação
        cleaned = re.sub(r'[R$\s\(\)]', '', str(value))
        cleaned = cleaned.replace('.', '').replace(',', '.')
        cleaned = cleaned.strip()
        try:
            float(cleaned)
            return True
        except:
            return False
    
    def _identify_metric(self, text: str) -> Optional[str]:
        """Identifica métrica a partir do texto"""
        for metric_name, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    return metric_name
        return None
    
    def _extract_value(self, row: pd.Series, numeric_columns: List[int]) -> Optional[float]:
        """Extrai valor numérico da linha"""
        for col in numeric_columns:
            val = row.iloc[col]
            if pd.isna(val):
                continue
            
            val_str = str(val).strip()
            if not val_str:
                continue
            
            # Limpa o valor
            cleaned = val_str
            # Remove R$ e espaços
            cleaned = re.sub(r'R\$\s*', '', cleaned)
            # Remove parênteses (valores negativos)
            negative = '(' in cleaned and ')' in cleaned
            cleaned = re.sub(r'[\(\)]', '', cleaned)
            # Remove pontos de milhar
            cleaned = cleaned.replace('.', '')
            # Substitui vírgula decimal
            cleaned = cleaned.replace(',', '.')
            cleaned = cleaned.strip()
            
            # Extrai número
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
        """Tenta extrair página da linha ou DataFrame"""
        if '_page' in df.columns:
            return row.get('_page')
        return None


# Instância global
semantic_parser = SemanticFinancialParser()