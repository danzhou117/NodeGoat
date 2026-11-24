import pytest

from helpers import SEED_USERS, page_text


def test_profile_page(user1):
    response = user1.get("/profile")
    text = page_text(response)
    assert response.status_code == 200
    assert "Edit Profile" in text
    assert "John Doe" in text


def test_valid_profile_update(user1, db):
    data = {
        "firstName": "Johnny",
        "lastName": "Doer",
        "ssn": "123-45-6789",
        "dob": "1990-01-15",
        "address": "1 Main St",
        "bankAcc": "12345678",
        "bankRouting": "0198212#",
        "website": "https://example.com",
    }
    response = user1.post("/profile", data=data)
    assert response.status_code == 200
    assert "Profile updated successfully." in page_text(response)
    assert "Johnny Doer" in page_text(response)
    user = db.users.find_one({"_id": 2})
    expected = dict(SEED_USERS[1])
    expected.update({key: data[key] for key in ("firstName", "lastName", "ssn", "dob", "address", "bankAcc", "bankRouting")})
    assert user == expected
    for field in ("firstName", "lastName", "ssn", "dob", "address", "bankAcc", "bankRouting"):
        assert type(user[field]) is str
    assert user["bankAcc"] == "12345678"
    assert "website" not in user
    assert db.users.find_one({"_id": 3}) == SEED_USERS[2]


def test_blank_profile_names_are_not_overwritten(user1, db):
    response = user1.post(
        "/profile",
        data={"firstName": "", "lastName": "", "ssn": "123-45-6789", "bankRouting": "0198212#"},
    )
    assert response.status_code == 200
    assert "Profile updated successfully." in page_text(response)
    user = db.users.find_one({"_id": 2})
    assert user["firstName"] == "John"
    assert user["lastName"] == "Doe"
    assert type(user["firstName"]) is str
    assert type(user["lastName"]) is str
    assert user["ssn"] == "123-45-6789"
    assert type(user["ssn"]) is str
    assert user["bankRouting"] == "0198212#"
    assert type(user["bankRouting"]) is str


@pytest.mark.parametrize("routing", ["0198212", "abc#", ""])
def test_invalid_routing_does_not_write(user1, db, routing):
    response = user1.post(
        "/profile",
        data={"firstName": "Johnny", "lastName": "Doer", "ssn": "123-45-6789", "bankRouting": routing},
    )
    text = page_text(response)
    assert response.status_code == 200
    assert "Bank Routing number does not comply with requirements for format specified" in text
    assert "Profile updated successfully." not in text
    assert db.users.find_one({"_id": 2}) == SEED_USERS[1]


def test_unanchored_routing_regex_is_pinned(user1, db):
    """Pins the unanchored routing regex behavior."""
    response = user1.post(
        "/profile",
        data={"firstName": "Johnny", "lastName": "Doer", "bankRouting": "abc123#xyz"},
    )
    assert response.status_code == 200
    assert "Profile updated successfully." in page_text(response)
    user = db.users.find_one({"_id": 2})
    assert user["bankRouting"] == "abc123#xyz"
    assert type(user["bankRouting"]) is str
