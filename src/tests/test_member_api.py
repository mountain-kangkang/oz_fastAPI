# def test_example(sample_data):
#     assert sample_data["hello"] == "world"
import base64

from member.models import Member


def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"ping": "pong"}

def test_user_sign_up(client, test_session):
    # given

    # when
    response = client.post(
        "/sync/members",
        json={"username": "test_user", "password": "pw"},
    )

    # then
    assert response.status_code == 201

    assert response.json()["id"]
    assert response.json()["username"] == "test_user"
    assert response.json()["password"]

    assert test_session.query(Member).filter(Member.username == "test_user").first()


def test_user_login(client, test_session, test_user):
    # given

    # when
    credentials = b"test_user:pw"
    encoded_bytes = base64.b64encode(credentials)

    response = client.post(
        "/sync/members/login",
        headers={"Authorization": "Basic " + encoded_bytes.decode("utf-8")},
    )

    # then
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_get_me(client, test_session, test_user, test_access_token):
    # given

    # when
    response = client.get(
        "/sync/members/me",
        headers={"Authorization": "Bearer " + test_access_token},
    )

    # then
    assert response.status_code == 200
    assert response.json()["id"] == test_user.id
    assert response.json()["username"] == test_user.username
    assert response.json()["password"] == test_user.password


def test_update_me(client, test_session, test_user, test_access_token):
    # given
    old_password = test_user.password

    # when
    response = client.patch(
        "/sync/members/me",
        json={"new_password": "new_pw"},
        headers={"Authorization": "Bearer " + test_access_token},
    )

    # then
    assert response.status_code == 200
    assert response.json()["id"] == test_user.id
    assert response.json()["username"] == test_user.username
    assert response.json()["password"] != old_password


def test_delete_me(client, test_session, test_access_token):
    # given

    # when
    response = client.delete(
        "/sync/members/me",
        headers={"Authorization": "Bearer " + test_access_token},
    )

    # then
    assert response.status_code == 204
