# Athena Financial API

API para consulta de dados financeiros com extração de PDF e RAG com Grok.

## Funcionalidades

- 🔍 Extração de dados de PDFs financeiros (ITR) com ensemble de parsers
- 💬 Consulta em linguagem natural
- 📄 Rastreabilidade completa (página + nota)
- 🧠 RAG com Grok para notas explicativas
- 🎨 Frontend simples para demonstração

## Stack

- FastAPI
- SQLAlchemy + SQLite
- pdfplumber / tabula / camelot
- Grok API (xAI)

## Instalação

```bash
git clone https://github.com/SEU_USUARIO/athena-financial-api.git
cd athena-financial-api
pip install -r requirements.txt
cp .env.example .env
python -m app.main