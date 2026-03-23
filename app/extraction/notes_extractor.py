import pdfplumber
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models import Note, Document


def extract_notes_from_pdf(pdf_path: str, document_id: str = None) -> List[Dict[str, Any]]:
    """
    Extrai notas explicativas do PDF
    """
    notes = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            current_note = None
            current_content = []
            current_page = None
            
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                
                for line in lines:
                    # Detecta início de nota (Nota X, Nota XX)
                    note_match = re.match(r'^Nota\s+(\d+)\s*[-–]\s*(.*)', line, re.IGNORECASE)
                    
                    if note_match:
                        # Salva nota anterior
                        if current_note and current_content:
                            notes.append({
                                "note_number": current_note,
                                "content": "\n".join(current_content),
                                "page_start": current_page,
                                "document_id": document_id
                            })
                        
                        # Inicia nova nota
                        current_note = note_match.group(1)
                        current_content = [note_match.group(2).strip()]
                        current_page = page_num
                    else:
                        if current_note:
                            current_content.append(line.strip())
            
            # Salva última nota
            if current_note and current_content:
                notes.append({
                    "note_number": current_note,
                    "content": "\n".join(current_content),
                    "page_start": current_page,
                    "document_id": document_id
                })
    
    except Exception as e:
        print(f"Erro ao extrair notas: {e}")
    
    return notes


def load_notes_to_database(pdf_path: str, document_id: str):
    """Carrega as notas extraídas para o banco"""
    db = SessionLocal()
    
    try:
        notes = extract_notes_from_pdf(pdf_path, document_id)
        count = 0
        
        for note_data in notes:
            existing = db.query(Note).filter(
                Note.document_id == document_id,
                Note.note_number == note_data["note_number"]
            ).first()
            
            if not existing:
                note = Note(
                    document_id=document_id,
                    note_number=note_data["note_number"],
                    content=note_data["content"][:5000],  # Limita tamanho
                    page_start=note_data["page_start"]
                )
                db.add(note)
                count += 1
        
        db.commit()
        print(f"📝 Carregadas {count} notas explicativas")
        return count
        
    except Exception as e:
        print(f"Erro ao carregar notas: {e}")
        db.rollback()
        return 0
    finally:
        db.close()