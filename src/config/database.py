from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# DATABASE_URL = "mysql+pymysql://root:ozcoding_pw@127.0.0.1:33060/ozcoding"
# DATABASE_URL = "mysql+pymysql://root:ozcoding_pw@localhost:33060/ozcoding?charset=utf8mb4"
DATABASE_URL = "mysql+pymysql://root:ozcoding_pw@localhost:9991/ozcoding"

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    connect_args={'connect_timeout': 10}
)
SessionFactory = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

Base = declarative_base()

def get_session():
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()