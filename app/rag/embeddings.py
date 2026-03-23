import re
import math
from typing import List, Dict, Set, Tuple
from collections import Counter

class SimpleEmbedding:
    """
    Gerador de embeddings baseado em TF-IDF.
    Simples e sem dependências externas.
    Para produção, usar sentence-transformers ou embeddings da Grok.
    """
    
    def __init__(self):
        self.stopwords = {
            'a', 'e', 'o', 'de', 'da', 'do', 'em', 'para', 'com', 'por', 'um', 'uma',
            'os', 'as', 'ao', 'aos', 'na', 'nas', 'no', 'nos', 'que', 'se', 'como',
            'mas', 'ou', 'ou', 'é', 'são', 'está', 'foram', 'ser', 'ter', 'há'
        }
        self.idf_cache = {}
        self.corpus = []
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokeniza o texto em palavras.
        """
        text = text.lower()
        # Remove pontuação
        text = re.sub(r'[^\w\s]', ' ', text)
        # Divide em palavras
        tokens = text.split()
        # Remove stopwords
        tokens = [t for t in tokens if t not in self.stopwords and len(t) > 2]
        return tokens
    
    def fit(self, documents: List[str]):
        """
        Treina o modelo com um corpus de documentos.
        Calcula IDF para cada termo.
        """
        self.corpus = documents
        doc_count = len(documents)
        
        # Conta quantos documentos contêm cada termo
        term_doc_count = Counter()
        
        for doc in documents:
            terms = set(self.tokenize(doc))
            for term in terms:
                term_doc_count[term] += 1
        
        # Calcula IDF
        for term, count in term_doc_count.items():
            self.idf_cache[term] = math.log(doc_count / (1 + count))
    
    def encode(self, text: str) -> Dict[str, float]:
        """
        Gera vetor TF-IDF para um texto.
        Retorna dicionário termo -> peso.
        """
        tokens = self.tokenize(text)
        term_freq = Counter(tokens)
        
        vector = {}
        for term, tf in term_freq.items():
            idf = self.idf_cache.get(term, math.log(len(self.corpus) + 1))
            vector[term] = tf * idf
        
        return vector
    
    def cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """
        Calcula similaridade de cosseno entre dois vetores.
        """
        common = set(vec1.keys()) & set(vec2.keys())
        if not common:
            return 0.0
        
        dot = sum(vec1[w] * vec2[w] for w in common)
        norm1 = math.sqrt(sum(v**2 for v in vec1.values()))
        norm2 = math.sqrt(sum(v**2 for v in vec2.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot / (norm1 * norm2)
    
    def search(self, query: str, documents: List[str], top_k: int = 5) -> List[Tuple[int, float]]:
        """
        Busca os documentos mais similares à query.
        """
        query_vec = self.encode(query)
        
        results = []
        for idx, doc in enumerate(documents):
            doc_vec = self.encode(doc)
            sim = self.cosine_similarity(query_vec, doc_vec)
            results.append((idx, sim))
        
        # Ordena por similaridade decrescente
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]


class NoteEmbedding:
    """
    Gerenciador de embeddings para notas explicativas.
    """
    
    def __init__(self):
        self.embedder = SimpleEmbedding()
        self.note_vectors = []
        self.note_texts = []
    
    def build_index(self, notes: List[Dict[str, str]]):
        """
        Constrói índice de embeddings a partir das notas.
        """
        self.note_texts = [note["content"] for note in notes]
        self.embedder.fit(self.note_texts)
        
        self.note_vectors = []
        for text in self.note_texts:
            vec = self.embedder.encode(text)
            self.note_vectors.append(vec)
        
        print(f"✅ Índice construído com {len(notes)} notas")
    
    def search(self, query: str, top_k: int = 3) -> List[Tuple[int, float]]:
        """
        Busca notas relevantes para a query.
        """
        query_vec = self.embedder.encode(query)
        
        results = []
        for idx, note_vec in enumerate(self.note_vectors):
            sim = self.embedder.cosine_similarity(query_vec, note_vec)
            results.append((idx, sim))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def search_with_text(self, query: str, notes: List[Dict[str, str]], top_k: int = 3) -> List[Dict]:
        """
        Busca e retorna as notas com conteúdo.
        """
        if not self.note_vectors:
            self.build_index(notes)
        
        results = self.search(query, top_k)
        
        return [
            {
                "index": idx,
                "similarity": sim,
                "content": notes[idx]["content"],
                "note_number": notes[idx].get("note_number", "N/A"),
                "page": notes[idx].get("page_start", None)
            }
            for idx, sim in results
        ]


# Instância global
note_embedding = NoteEmbedding()