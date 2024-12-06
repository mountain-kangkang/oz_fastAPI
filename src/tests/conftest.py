# fixture -> 테스트에 사용하는 예시 데이터, 기능
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists

from fastapi.testclient import TestClient
from main import app

from config.database import Base, get_session
from member.authentication import encode_access_token
from member.models import Member


# @pytest.fixture
# def sample_data():
#     return {"hello": "world"}

# 로컬 mysql -> db: ozcoding / test
# 회원 5명
# 테스트 코드

@pytest.fixture
def test_db():
    test_db_url = "mysql+pymysql://root:ozcoding_pw@localhost:9991/test"
    # test 데이터베이스 만들어줌
    if not database_exists(test_db_url):
        create_database(test_db_url)

    # Base의 metadata 기준으로 테이블 생성
    engine = create_engine(test_db_url)
    Base.metadata.create_all(engine)

    try:
        yield engine
    finally:
        Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def test_session(test_db):
    connection = test_db.engine.connect()
    connection.begin()
    session = sessionmaker()(bind=connection)

    try:
        yield session
    finally:
        session.rollback()
        connection.close()


@pytest.fixture
def client(test_session):
    def test_get_session():
        yield test_session

    app.dependency_overrides[get_session] = test_get_session

    return TestClient(app=app)


@pytest.fixture(scope="function")
def test_user(test_session):
    new_user = Member.create(username="test_user", password="pw")
    test_session.add(new_user)
    test_session.commit()
    return new_user

@pytest.fixture(scope="function")
def test_access_token(test_user):
    return encode_access_token(username=test_user.username)