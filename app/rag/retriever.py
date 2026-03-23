from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models import Note, Document
from app.rag.embeddings import note_embedding
from app.rag.grok_client import grok_client, grok_rag


class NoteRetriever:
    """
    Recupera notas explicativas relevantes para uma pergunta.
    """
    
    def __init__(self):
        self.cached_notes = []
        self.embeddings_built = False
    
    def _load_notes(self, document_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Carrega notas do banco de dados"""
        db = SessionLocal()
        try:
            query = db.query(Note)
            if document_id:
                query = query.filter(Note.document_id == document_id)
            
            notes = query.all()
            
            return [
                {
                    "id": n.id,
                    "note_number": n.note_number,
                    "title": n.title,
                    "content": n.content,
                    "page_start": n.page_start,
                    "document_id": n.document_id
                }
                for n in notes
            ]
        finally:
            db.close()
    
    def build_index(self, document_id: Optional[str] = None):
        """Constrói índice de embeddings para as notas"""
        notes = self._load_notes(document_id)
        if notes:
            note_embedding.build_index(notes)
            self.cached_notes = notes
            self.embeddings_built = True
        return notes
    
    def retrieve(
        self,
        question: str,
        document_id: Optional[str] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Recupera as notas mais relevantes para a pergunta.
        """
        # Carrega notas se necessário
        if not self.cached_notes or self.cached_notes[0].get("document_id") != document_id:
            self.build_index(document_id)
        
        if not self.cached_notes:
            return []
        
        # Busca por similaridade
        results = note_embedding.search_with_text(
            question,
            self.cached_notes,
            top_k
        )
        
        return [
            {
                "note_number": r["note_number"],
                "title": r.get("title", f"Nota {r['note_number']}"),
                "content": r["content"][:800],
                "page_start": r["page"],
                "similarity": r["similarity"]
            }
            for r in results
        ]
    
    def retrieve_and_answer(
        self,
        question: str,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Recupera contexto relevante e gera resposta via Grok.
        """
        # 1. Recupera notas relevantes
        notes = self.retrieve(question, document_id, top_k=2)
        
        if not notes:
            return {
                "answer": "Não encontrei informações relevantes nas notas explicativas.",
                "sources": []
            }
        
        # 2. Monta contexto
        context_parts = []
        sources = []
        
        for note in notes:
            context_parts.append(f"Nota {note['note_number']}:\n{note['content']}")
            sources.append({
                "note": note['note_number'],
                "page": note['page_start'],
                "similarity": round(note['similarity'], 3)
            })
        
        context = "\n\n".join(context_parts)
        
        # 3. Gera resposta com Grok
        answer = grok_rag.answer_with_context(
            question, 
            context, 
            sources[0].get("page") if sources else None
        )
        
        return {
            "answer": answer,
            "sources": sources
        }


# Instância global
note_retriever = NoteRetriever()