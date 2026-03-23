import os
import requests
import json
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class GrokClient:
    """
    Cliente para a API da Grok (xAI)
    Documentação: https://docs.x.ai
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROK_API_KEY")
        self.base_url = "https://api.x.ai/v1"
        
        if not self.api_key:
            print("⚠️ GROK_API_KEY não configurada. Usando modo fallback.")
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "grok-beta",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Optional[str]:
        """
        Envia uma conversa para a Grok e retorna a resposta
        """
        if not self.api_key:
            return self._fallback_response(messages)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        
        except Exception as e:
            print(f"Erro na chamada Grok: {e}")
            return self._fallback_response(messages)
    
    def _fallback_response(self, messages: List[Dict[str, str]]) -> str:
        """Resposta de fallback quando API não está disponível"""
        last_message = messages[-1]["content"] if messages else ""
        return f"[Modo offline] Pergunta recebida: '{last_message}'. Para respostas completas, configure GROK_API_KEY."


class GrokRAG:
    """
    RAG usando Grok para responder perguntas sobre notas explicativas
    """
    
    def __init__(self, grok_client: GrokClient):
        self.grok = grok_client
        self.system_prompt = """
Você é um assistente especializado em dados financeiros da Magazine Luiza.
Use apenas as informações fornecidas no contexto para responder.
Se a resposta não estiver no contexto, diga que não encontrou.
Sempre cite a página de origem quando disponível.
Responda em português de forma clara e objetiva.
"""
    
    def answer_with_context(
        self,
        question: str,
        context: str,
        source_page: Optional[int] = None
    ) -> str:
        """
        Gera resposta baseada no contexto fornecido
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"""
Contexto (página {source_page if source_page else 'desconhecida'}):
{context}

Pergunta: {question}

Responda com base APENAS no contexto acima.
"""}
        ]
        
        return self.grok.chat_completion(messages)


# Instância global
grok_client = GrokClient()
grok_rag = GrokRAG(grok_client)