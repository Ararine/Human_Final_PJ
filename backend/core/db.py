from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://1team:1team@localhost:5432/1team"

engine = create_engine(DATABASE_URL)


def get_connection():
    return engine.connect()