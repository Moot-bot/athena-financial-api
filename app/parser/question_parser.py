import re
from typing import Dict, Optional, List, Tuple

class QuestionParser:
    """
    Interpretador de perguntas em linguagem natural.
    Extrai métrica, empresa, período e escopo.
    """
    
    # Mapeamento de sinônimos para métricas
    METRIC_MAPPING = {
        # Receitas
        "receita": "Receita líquida de vendas",
        "receita líquida": "Receita líquida de vendas",
        "receita bruta": "Receita líquida de vendas",
        "vendas": "Receita líquida de vendas",
        "faturamento": "Receita líquida de vendas",
        
        # Lucros
        "lucro bruto": "Lucro bruto",
        "lucro líquido": "Lucro líquido do período",
        "lucro": "Lucro líquido do período",
        "resultado": "Lucro líquido do período",
        
        # Dívida
        "divida": "Empréstimos e financiamentos",
        "dívida": "Empréstimos e financiamentos",
        "endividamento": "Empréstimos e financiamentos",
        "empréstimos": "Empréstimos e financiamentos",
        
        # Patrimônio
        "patrimônio": "Patrimônio líquido",
        "patrimonio": "Patrimônio líquido",
        "pl": "Patrimônio líquido",
        
        # Ativo
        "ativo total": "Ativo total",
        "ativo": "Ativo total",
        "caixa": "Disponibilidades",
        "disponibilidades": "Disponibilidades",
        
        # Fluxo de caixa
        "fluxo operacional": "Fluxo de caixa operacional",
        "fluxo de caixa operacional": "Fluxo de caixa operacional",
        "fco": "Fluxo de caixa operacional",
    }
    
    # Mapeamento de empresas
    COMPANY_MAPPING = {
        "magazine luiza": "Magazine Luiza",
        "magalu": "Magazine Luiza",
        "mglu3": "Magazine Luiza",
    }
    
    # Padrões de período
    PERIOD_PATTERNS = [
        (r'(\d)t\s*(\d{2})', 'quarter'),      # 1T22, 1T 22
        (r'(\d)º?\s*trimestre\s+de\s+(\d{4})', 'quarter_full'),  # 1º trimestre de 2022
        (r'(\d{4})', 'year'),                   # 2022
    ]
    
    def __init__(self):
        self.metric_mapping = self.METRIC_MAPPING
        self.company_mapping = self.COMPANY_MAPPING
    
    def parse(self, question: str) -> Dict:
        """
        Extrai os parâmetros da pergunta.
        
        Args:
            question: Pergunta em linguagem natural
            
        Returns:
            Dict com metric, company, year, quarter, scope
        """
        q = question.lower().strip()
        
        result = {
            "metric": None,
            "company": None,
            "year": None,
            "quarter": None,
            "scope": "Consolidado",  # default
            "raw_question": question
        }
        
        # 1. Extrair métrica
        result["metric"] = self._extract_metric(q)
        
        # 2. Extrair empresa
        result["company"] = self._extract_company(q)
        
        # 3. Extrair período
        year, quarter = self._extract_period(q)
        result["year"] = year
        result["quarter"] = quarter
        
        # 4. Extrair escopo
        result["scope"] = self._extract_scope(q)
        
        return result
    
    def _extract_metric(self, text: str) -> Optional[str]:
        """Extrai a métrica da pergunta"""
        for keyword, metric_name in self.metric_mapping.items():
            if keyword in text:
                return metric_name
        return None
    
    def _extract_company(self, text: str) -> Optional[str]:
        """Extrai a empresa da pergunta"""
        for keyword, company_name in self.company_mapping.items():
            if keyword in text:
                return company_name
        return None
    
    def _extract_period(self, text: str) -> Tuple[Optional[int], Optional[int]]:
        """Extrai ano e trimestre da pergunta"""
        year = None
        quarter = None
        
        for pattern, pattern_type in self.PERIOD_PATTERNS:
            match = re.search(pattern, text)
            if match:
                if pattern_type == 'quarter':
                    quarter = int(match.group(1))
                    year_suffix = match.group(2)
                    year = 2000 + int(year_suffix) if int(year_suffix) >= 20 else 1900 + int(year_suffix)
                    break
                elif pattern_type == 'quarter_full':
                    quarter = int(match.group(1))
                    year = int(match.group(2))
                    break
                elif pattern_type == 'year':
                    year = int(match.group(1))
                    break
        
        return year, quarter
    
    def _extract_scope(self, text: str) -> str:
        """Extrai o escopo da pergunta"""
        if "controladora" in text:
            return "Controladora"
        elif "consolidado" in text:
            return "Consolidado"
        return "Consolidado"  # default
    
    def get_available_metrics(self) -> List[str]:
        """Retorna lista de métricas disponíveis"""
        return list(set(self.metric_mapping.values()))
    
    def validate(self, parsed: Dict) -> Tuple[bool, Optional[str]]:
        """Valida se os parâmetros extraídos são suficientes"""
        if not parsed["metric"]:
            return False, "Não foi possível identificar a métrica. Use: receita, lucro, dívida, etc."
        
        if not parsed["company"]:
            return False, "Não foi possível identificar a empresa. Use: Magazine Luiza, Magalu"
        
        if not parsed["year"]:
            return False, "Não foi possível identificar o período. Use: 1T22, 2022, etc."
        
        return True, None


# Instância global para uso na API
parser = QuestionParser()