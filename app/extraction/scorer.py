import re
import pandas as pd
from typing import List, Optional, Tuple

class FinancialTableScorer:
    """
    Avalia a qualidade de uma tabela extraída com base em critérios financeiros.
    """
    
    # Palavras-chave que indicam demonstrações financeiras
    FINANCIAL_KEYWORDS = [
        "receita", "lucro", "caixa", "ativo", "passivo", "patrimônio",
        "resultado", "despesa", "custo", "estoque", "divida", "empréstimo",
        "balanço", "dre", "dfc", "fluxo", "controladora", "consolidado",
        "circulante", "não circulante", "patrimônio líquido"
    ]
    
    # Padrões de valores monetários
    MONETARY_PATTERNS = [
        r'R\$\s*\d+',           # R$ 1000
        r'\d+\.\d{3}\.\d{3}',   # 1.000.000
        r'\d+\.\d{3}',          # 1.000
        r'\(\d+\)',             # (1000) - valores negativos
        r'-\d+',                # -1000
    ]
    
    def __init__(self):
        self.keywords_lower = [kw.lower() for kw in self.FINANCIAL_KEYWORDS]
    
    def score(self, df: pd.DataFrame) -> float:
        """
        Calcula score de qualidade da tabela.
        Retorna valor entre 0 e 100.
        """
        if df is None or df.empty:
            return 0.0
        
        score = 0.0
        
        # Converte para string para análise
        df_str = df.astype(str)
        all_text = " ".join(df_str.values.flatten()).lower()
        
        # 1. Presença de palavras-chave financeiras (max 35 pts)
        keyword_score = 0
        for kw in self.keywords_lower:
            if kw in all_text:
                keyword_score += 2
        
        keyword_score = min(keyword_score, 35)
        score += keyword_score
        
        # 2. Densidade numérica (max 25 pts)
        numeric_count = 0
        total = df.size
        
        for val in df.values.flatten():
            if self._is_numeric(str(val)):
                numeric_count += 1
        
        density = numeric_count / total if total > 0 else 0
        score += density * 25
        
        # 3. Estrutura: pelo menos 3 colunas (10 pts)
        if df.shape[1] >= 3:
            score += 10
        
        # 4. Linhas com texto + número (max 20 pts)
        mixed_rows = 0
        for _, row in df.iterrows():
            row_text = " ".join(str(x) for x in row)
            has_text = bool(re.search(r'[a-zA-ZÀ-ÿ]', row_text))
            has_number = bool(re.search(r'\d', row_text))
            if has_text and has_number:
                mixed_rows += 1
        
        mixed_ratio = mixed_rows / df.shape[0] if df.shape[0] > 0 else 0
        score += mixed_ratio * 20
        
        # 5. Bônus: estrutura hierárquica (5 pts)
        if self._has_hierarchical_structure(df):
            score += 5
        
        # 6. Bônus: presença de valores negativos (5 pts)
        if self._has_negative_values(df):
            score += 5
        
        return min(score, 100.0)
    
    def _is_numeric(self, value: str) -> bool:
        """Verifica se string parece um número"""
        cleaned = value.strip()
        if not cleaned:
            return False
        
        # Remove formatação monetária
        cleaned = re.sub(r'[R$\s\(\)\-\.]', '', cleaned)
        cleaned = cleaned.replace(',', '.')
        
        try:
            float(cleaned)
            return True
        except:
            return False
    
    def _has_hierarchical_structure(self, df: pd.DataFrame) -> bool:
        """Verifica se a tabela tem estrutura hierárquica (indentação)"""
        first_col = df.iloc[:, 0].astype(str)
        
        # Verifica se há linhas com espaços/indentação
        has_indentation = any('  ' in str(val) for val in first_col)
        
        # Verifica palavras comuns em hierarquias
        hierarchy_keywords = ['total', 'subtotal', 'líquido', 'bruto']
        has_keywords = any(kw in ' '.join(first_col).lower() for kw in hierarchy_keywords)
        
        return has_indentation or has_keywords
    
    def _has_negative_values(self, df: pd.DataFrame) -> bool:
        """Verifica se há valores negativos na tabela"""
        for val in df.values.flatten():
            val_str = str(val)
            if '(' in val_str or '-' in val_str:
                # Tenta extrair número
                num_match = re.search(r'\(?(\d+[\.,]?\d*)', val_str)
                if num_match:
                    return True
        return False
    
    def score_all_tables(self, tables: List[pd.DataFrame]) -> List[Tuple[float, pd.DataFrame, int]]:
        """
        Aplica score a todas as tabelas e retorna lista ordenada.
        """
        scored = []
        for idx, table in enumerate(tables):
            if table is not None and not table.empty:
                s = self.score(table)
                scored.append((s, table, idx))
        
        # Ordena por score decrescente
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored
    
    def get_best_table(self, tables: List[pd.DataFrame]) -> Optional[pd.DataFrame]:
        """Retorna a melhor tabela da lista"""
        scored = self.score_all_tables(tables)
        if scored:
            return scored[0][1]
        return None


# Instância global
table_scorer = FinancialTableScorer()