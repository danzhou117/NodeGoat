from helpers import SEED_USERS, page_text


def test_admin_benefits_list(admin):
    response = admin.get("/benefits")
    text = page_text(response)
    assert response.status_code == 200
    assert "Benefits Start Date" in text
    assert "2 John Doe" in text
    assert "3 Will Smith" in text
    assert "Node Goat Admin" not in text
    assert 'value="2030-01-10"' in response.text
    assert 'value="2025-11-30"' in response.text


def test_admin_can_update_benefits(admin, db):
    response = admin.post(
        "/benefits",
        data={"userId": "2", "benefitStartDate": "2031-05-20"},
    )
    assert response.status_code == 200
    assert "Benefits updated successfully." in page_text(response)
    assert 'value="2031-05-20"' in response.text
    user = db.users.find_one({"_id": 2})
    expected = dict(SEED_USERS[1])
    expected["benefitStartDate"] = "2031-05-20"
    assert user == expected
    assert type(user["_id"]) is int
    assert type(user["benefitStartDate"]) is str
    assert db.users.find_one({"_id": 3}) == SEED_USERS[2]


def test_non_admin_can_update_benefits(user1, db):
    """Pins the missing function-level authorization on benefits."""
    response = user1.get("/benefits")
    assert response.status_code == 200
    assert "Benefits Start Date" in page_text(response)
    response = user1.post(
        "/benefits",
        data={"userId": "3", "benefitStartDate": "2032-06-21"},
    )
    assert response.status_code == 200
    assert "Benefits updated successfully." in page_text(response)
    user = db.users.find_one({"_id": 3})
    expected = dict(SEED_USERS[2])
    expected["benefitStartDate"] = "2032-06-21"
    assert user == expected
    assert type(user["_id"]) is int
    assert type(user["benefitStartDate"]) is str
