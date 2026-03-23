from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

# Configuração - pode vir de variáveis de ambiente
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///finance.db")

# Configurações específicas por banco
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # necessário para SQLite
        echo=False
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        echo=False
    )

# Fábrica de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Dependência para obter sessão do banco"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Cria todas as tabelas no banco"""
    from app.models import Base
    Base.metadata.create_all(bind=engine)

def drop_db():
    """Remove todas as tabelas (cuidado!)"""
    from app.models import Base
    Base.metadata.drop_all(bind=engine)