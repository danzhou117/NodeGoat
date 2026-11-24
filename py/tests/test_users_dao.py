import re
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from nodegoat.dao.users import InvalidPasswordError, NoSuchUserError, UserDAO
from conftest import field_types

USER_FIELDS = [
    ("_id", "int"),
    ("userName", "string"),
    ("firstName", "string"),
    ("lastName", "string"),
    ("benefitStartDate", "string"),
    ("password", "string"),
]


def test_seed_comes_from_db_reset(db):
    assert db.counters.find_one() == {"_id": "userId", "seq": 3}
    assert db.users.count_documents({}) == 3
    assert db.users.find_one({"_id": 1})["userName"] == "admin"
    assert db.users.find_one({"_id": 2})["userName"] == "user1"
    assert db.users.find_one({"_id": 3})["userName"] == "user2"


@pytest.mark.parametrize("email", ["a@example.com", ""])
def test_add_user_matches_node_written_doc(db, user_dao, run_node, email):
    run_node("py/tests/node_add_user.js", "nodeuser", "Node", "User", "Node_123", email)
    user_dao.add_user("pyuser", "Py", "User", "Py_123", email)
    node_fields = field_types(db, {"userName": "nodeuser"})
    python_fields = field_types(db, {"userName": "pyuser"})
    expected = USER_FIELDS + ([("email", "string")] if email else [])
    assert python_fields == node_fields == expected
    assert db.users.find_one({"userName": "nodeuser"})["_id"] == 4
    assert db.users.find_one({"userName": "pyuser"})["_id"] == 5


def test_add_user_without_email_omits_field(user_dao, db):
    user_dao.add_user("pyuser-none", "Py", "User", "Py_123", None)
    user_dao.add_user("pyuser-default", "Py", "User", "Py_123")
    assert "email" not in db.users.find_one({"userName": "pyuser-none"})
    assert "email" not in db.users.find_one({"userName": "pyuser-default"})


def test_add_user_returns_stored_doc(user_dao, db):
    returned = user_dao.add_user("pyuser", "Py", "User", "Py_123")
    stored = db.users.find_one({"_id": returned["_id"]})
    assert returned == stored
    assert type(returned["_id"]) is int
    assert stored["password"] == "Py_123"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", stored["benefitStartDate"])


def test_add_user_ids_come_from_counter(user_dao, db):
    assert user_dao.add_user("pyuser1", "Py", "User", "Py_123")["_id"] == 4
    assert user_dao.add_user("pyuser2", "Py", "User", "Py_123")["_id"] == 5
    assert db.counters.find_one() == {"_id": "userId", "seq": 5}
    type_result = next(
        db.counters.aggregate(
            [{"$project": {"type": {"$type": "$seq"}}}],
        )
    )
    assert type_result["type"] == "int"


def test_double_counter_still_yields_int32_id_like_node(db, user_dao, run_node):
    db.counters.replace_one({"_id": "userId"}, {"_id": "userId", "seq": 3.0})
    run_node("py/tests/node_add_user.js", "nodeuser", "Node", "User", "Node_123", "")
    user_dao.add_user("pyuser", "Py", "User", "Py_123", "")
    assert field_types(db, {"userName": "nodeuser"})[0] == ("_id", "int")
    assert field_types(db, {"userName": "pyuser"})[0] == ("_id", "int")


def test_get_next_sequence(user_dao):
    first = user_dao.get_next_sequence("userId")
    second = user_dao.get_next_sequence("userId")
    assert first == 4
    assert second == 5
    assert type(second) is int


def test_get_next_sequence_missing_counter_raises(user_dao, db):
    with pytest.raises(TypeError):
        user_dao.get_next_sequence("missing")
    assert db.counters.count_documents({}) == 1


@pytest.mark.parametrize("user_id", [2, "2", " 2", "2abc", "2.9", 2.9])
def test_get_user_by_id(user_dao, user_id):
    assert user_dao.get_user_by_id(user_id)["userName"] == "user1"


@pytest.mark.parametrize("user_id", ["abc", "", None, 999, "99999999999999999999999"])
def test_get_user_by_id_not_found(user_dao, user_id):
    assert user_dao.get_user_by_id(user_id) is None


def test_get_user_by_user_name(user_dao):
    assert user_dao.get_user_by_user_name("user1")["_id"] == 2
    assert user_dao.get_user_by_user_name("nobody") is None
    assert user_dao.get_user_by_user_name({"$in": ["admin"]})["userName"] == "admin"


def test_validate_login_success(user_dao):
    user = user_dao.validate_login("user1", "User1_123")
    assert user["_id"] == 2
    assert set(user) == {"_id", "userName", "firstName", "lastName", "benefitStartDate", "password"}


def test_validate_login_invalid_password(user_dao):
    with pytest.raises(InvalidPasswordError) as caught:
        user_dao.validate_login("user1", "wrong")
    assert str(caught.value) == "Invalid password"
    assert caught.value.invalid_password is True
    assert not isinstance(caught.value, NoSuchUserError)


def test_validate_login_no_such_user(user_dao):
    with pytest.raises(NoSuchUserError) as caught:
        user_dao.validate_login("nobody", "wrong")
    assert str(caught.value) == "User: null does not exist"
    assert caught.value.no_such_user is True
    assert not isinstance(caught.value, InvalidPasswordError)


def test_validate_login_operator_user_name(user_dao):
    assert user_dao.validate_login({"$in": ["admin"]}, "Admin_123")["userName"] == "admin"


def test_validate_login_password_is_type_strict(user_dao, db):
    db.users.update_one({"userName": "user1"}, {"$set": {"password": 123}})
    with pytest.raises(InvalidPasswordError):
        user_dao.validate_login("user1", "123")
    assert user_dao.validate_login("user1", 123)["_id"] == 2


def test_get_random_future_date_reproduces_node_arithmetic(monkeypatch):
    class StubDatetime:
        @classmethod
        def now(cls):
            return datetime(2026, 11, 22)

    monkeypatch.setattr("nodegoat.dao.users.datetime", StubDatetime)
    dao = UserDAO(MagicMock())
    monkeypatch.setattr("nodegoat.dao.users.random.random", lambda: 0.0)
    assert dao.get_random_future_date() == "2026-10-00"
    monkeypatch.setattr("nodegoat.dao.users.random.random", lambda: 0.999)
    assert dao.get_random_future_date() == "2056-07-09"
