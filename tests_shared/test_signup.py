from datetime import datetime, timedelta, timezone
import re

import pytest
from bson import ObjectId

from helpers import page_text, wait_for


def signup_data(user_name, first_name="New", last_name="User", password="NewUser_123", verify=None, email="new@example.com"):
    return {
        "userName": user_name,
        "firstName": first_name,
        "lastName": last_name,
        "password": password,
        "verify": password if verify is None else verify,
        "email": email,
    }


def test_signup_page(anon):
    response = anon.get("/signup")
    assert response.status_code == 200
    assert "Enter sign up information" in page_text(response)


def test_valid_signup_renders_dashboard_and_persists(anon, login, db):
    data = signup_data("newuser")
    response = anon.post("/signup", data=data)
    assert response.status_code == 200
    assert "Total Retirement Savings" in page_text(response)
    assert "New User" in page_text(response)
    assert 'href="/allocations/4"' in response.text
    user = db.users.find_one({"userName": "newuser"})
    assert user["_id"] == 4
    assert type(user["_id"]) is int
    assert set(user) == {
        "_id", "userName", "firstName", "lastName", "benefitStartDate", "password", "email"
    }
    assert user["userName"] == data["userName"]
    assert user["firstName"] == data["firstName"]
    assert user["lastName"] == data["lastName"]
    assert user["password"] == data["password"]
    assert type(user["password"]) is str
    assert user["email"] == data["email"]
    assert type(user["email"]) is str
    assert type(user["benefitStartDate"]) is str
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", user["benefitStartDate"])
    date_parts = [int(part) for part in user["benefitStartDate"].split("-")]
    assert 0 <= date_parts[1] <= 11
    assert 0 <= date_parts[2] <= 28
    years = {
        (datetime.now(timezone.utc) + timedelta(days=days)).year for days in (-1, 0, 1)
    }
    assert min(years) + 1 <= date_parts[0] <= max(years) + 30
    assert db.counters.find_one({"_id": "userId"}) == {"_id": "userId", "seq": 4}
    assert type(db.counters.find_one({"_id": "userId"})["seq"]) is int
    allocation = wait_for(lambda: db.allocations.find_one({"userId": 4}))
    assert set(allocation) == {"_id", "userId", "stocks", "funds", "bonds"}
    assert type(allocation["_id"]) is ObjectId
    assert type(allocation["userId"]) is int
    assert type(allocation["stocks"]) is int
    assert type(allocation["funds"]) is int
    assert type(allocation["bonds"]) is int
    assert 1 <= allocation["stocks"] <= 40
    assert 1 <= allocation["funds"] <= 40
    assert allocation["bonds"] == 100 - allocation["stocks"] - allocation["funds"]
    assert db.allocations.count_documents({}) == 4
    assert "Total Retirement Savings" in page_text(anon.get("/dashboard"))
    fresh = login("newuser", "NewUser_123")
    assert fresh.get("/dashboard").status_code == 200


def test_signup_empty_email_accepts_weak_password(anon, db):
    """Pins acceptance of weak plaintext passwords and omission of empty email."""
    data = signup_data("weakuser", password="pw", email="")
    response = anon.post("/signup", data=data)
    assert response.status_code == 200
    assert "Total Retirement Savings" in page_text(response)
    user = db.users.find_one({"userName": "weakuser"})
    assert type(user["_id"]) is int
    assert set(user) == {
        "_id", "userName", "firstName", "lastName", "benefitStartDate", "password"
    }
    assert user["userName"] == data["userName"]
    assert type(user["userName"]) is str
    assert user["firstName"] == data["firstName"]
    assert type(user["firstName"]) is str
    assert user["lastName"] == data["lastName"]
    assert type(user["lastName"]) is str
    assert user["password"] == "pw"
    assert type(user["password"]) is str
    assert type(user["benefitStartDate"]) is str
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", user["benefitStartDate"])
    weak_date_parts = [int(part) for part in user["benefitStartDate"].split("-")]
    assert 0 <= weak_date_parts[1] <= 11
    assert 0 <= weak_date_parts[2] <= 28
    weak_years = {
        (datetime.now(timezone.utc) + timedelta(days=days)).year for days in (-1, 0, 1)
    }
    assert min(weak_years) + 1 <= weak_date_parts[0] <= max(weak_years) + 30
    allocation = wait_for(lambda: db.allocations.find_one({"userId": 4}))
    assert set(allocation) == {"_id", "userId", "stocks", "funds", "bonds"}
    assert type(allocation["_id"]) is ObjectId
    assert type(allocation["userId"]) is int
    assert type(allocation["stocks"]) is int
    assert type(allocation["funds"]) is int
    assert type(allocation["bonds"]) is int
    assert 1 <= allocation["stocks"] <= 40
    assert 1 <= allocation["funds"] <= 40
    assert allocation["bonds"] == 100 - allocation["stocks"] - allocation["funds"]
    assert db.allocations.count_documents({}) == 4


def test_two_signups_increment_ids_and_counter(anon, db):
    first = signup_data("firstuser", email="first@example.com")
    response = anon.post("/signup", data=first)
    assert response.status_code == 200
    assert "Total Retirement Savings" in page_text(response)
    first_user = db.users.find_one({"userName": "firstuser"})
    assert first_user["_id"] == 4
    assert type(first_user["_id"]) is int
    assert set(first_user) == {
        "_id", "userName", "firstName", "lastName", "benefitStartDate", "password", "email"
    }
    assert first_user["userName"] == first["userName"]
    assert first_user["firstName"] == first["firstName"]
    assert first_user["lastName"] == first["lastName"]
    assert first_user["password"] == first["password"]
    assert type(first_user["password"]) is str
    assert first_user["email"] == first["email"]
    assert type(first_user["email"]) is str
    assert type(first_user["benefitStartDate"]) is str
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", first_user["benefitStartDate"])
    first_date_parts = [int(part) for part in first_user["benefitStartDate"].split("-")]
    assert 0 <= first_date_parts[1] <= 11
    assert 0 <= first_date_parts[2] <= 28
    first_years = {
        (datetime.now(timezone.utc) + timedelta(days=days)).year for days in (-1, 0, 1)
    }
    assert min(first_years) + 1 <= first_date_parts[0] <= max(first_years) + 30
    first_allocation = wait_for(lambda: db.allocations.find_one({"userId": 4}))
    assert set(first_allocation) == {"_id", "userId", "stocks", "funds", "bonds"}
    assert type(first_allocation["_id"]) is ObjectId
    assert type(first_allocation["userId"]) is int
    assert type(first_allocation["stocks"]) is int
    assert type(first_allocation["funds"]) is int
    assert type(first_allocation["bonds"]) is int
    assert 1 <= first_allocation["stocks"] <= 40
    assert 1 <= first_allocation["funds"] <= 40
    assert first_allocation["bonds"] == 100 - first_allocation["stocks"] - first_allocation["funds"]
    assert db.allocations.count_documents({}) == 4
    second = signup_data("seconduser", email="second@example.com")
    response = anon.post("/signup", data=second)
    assert response.status_code == 200
    assert "Total Retirement Savings" in page_text(response)
    second_user = db.users.find_one({"userName": "seconduser"})
    assert second_user["_id"] == 5
    assert type(second_user["_id"]) is int
    assert set(second_user) == {
        "_id", "userName", "firstName", "lastName", "benefitStartDate", "password", "email"
    }
    assert second_user["userName"] == second["userName"]
    assert second_user["firstName"] == second["firstName"]
    assert second_user["lastName"] == second["lastName"]
    assert second_user["password"] == second["password"]
    assert type(second_user["password"]) is str
    assert second_user["email"] == second["email"]
    assert type(second_user["email"]) is str
    assert type(second_user["benefitStartDate"]) is str
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", second_user["benefitStartDate"])
    second_date_parts = [int(part) for part in second_user["benefitStartDate"].split("-")]
    assert 0 <= second_date_parts[1] <= 11
    assert 0 <= second_date_parts[2] <= 28
    second_years = {
        (datetime.now(timezone.utc) + timedelta(days=days)).year for days in (-1, 0, 1)
    }
    assert min(second_years) + 1 <= second_date_parts[0] <= max(second_years) + 30
    second_allocation = wait_for(lambda: db.allocations.find_one({"userId": 5}))
    assert set(second_allocation) == {"_id", "userId", "stocks", "funds", "bonds"}
    assert type(second_allocation["_id"]) is ObjectId
    assert type(second_allocation["userId"]) is int
    assert type(second_allocation["stocks"]) is int
    assert type(second_allocation["funds"]) is int
    assert type(second_allocation["bonds"]) is int
    assert 1 <= second_allocation["stocks"] <= 40
    assert 1 <= second_allocation["funds"] <= 40
    assert second_allocation["bonds"] == 100 - second_allocation["stocks"] - second_allocation["funds"]
    assert db.allocations.count_documents({}) == 5
    assert db.counters.find_one({"_id": "userId"}) == {"_id": "userId", "seq": 5}
    assert type(db.counters.find_one({"_id": "userId"})["seq"]) is int


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (signup_data("user1"), "User name already in use. Please choose another"),
        (signup_data("newuser", verify="different"), "Password must match"),
        (signup_data("newuser", email="not-an-email"), "Invalid email address"),
        (signup_data("newuser", password="A" * 21), "Password must be 8 to 18 characters including numbers, lowercase and uppercase letters."),
    ],
)
def test_signup_validation_errors(anon, db, data, message):
    response = anon.post("/signup", data=data)
    assert response.status_code == 200
    assert "Enter sign up information" in page_text(response)
    assert message in page_text(response)
    assert db.users.count_documents({}) == 3
    assert db.counters.find_one({"_id": "userId"}) == {"_id": "userId", "seq": 3}
    assert db.allocations.count_documents({}) == 3
