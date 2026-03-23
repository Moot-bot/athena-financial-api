from app.database.connection import get_db, init_db, SessionLocal
from app.database.queries import *
from app.database.seed import seed_data, run_seed, ensure_magalu_company, ensure_basic_metrics