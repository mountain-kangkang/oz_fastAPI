# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# DATABASE_URL = "mysql+pymysql://root:ozcoding_pw@127.0.0.1:33060/ozcoding"
# DATABASE_URL = "mysql+pymysql://root:ozcoding_pw@localhost:33060/ozcoding?charset=utf8mb4"
DATABASE_URL = "mysql+aiomysql://root:ozcoding_pw@localhost:9991/ozcoding"

async_engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    connect_args={'connect_timeout': 10}
)
AsyncSessionFactory = async_sessionmaker(
    bind=async_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,

)

async def get_async_session():
    session = AsyncSessionFactory()
    try:
        yield session
    finally:
        await session.close()   # db에 커넥션 종료