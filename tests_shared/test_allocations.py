from helpers import page_text


def test_own_allocations(user1, db):
    allocation = db.allocations.find_one({"userId": 2})
    response = user1.get("/allocations/2")
    text = page_text(response)
    assert response.status_code == 200
    assert "Asset Allocations for John Doe" in text
    assert f"Domestic Stocks : {allocation['stocks']} %" in text
    assert f"Funds: {allocation['funds']} %" in text
    assert f"Bonds: {allocation['bonds']} %" in text


def test_other_users_allocations_are_visible(user1, db):
    """Pins the insecure direct object reference in allocation URLs."""
    allocation = db.allocations.find_one({"userId": 3})
    response = user1.get("/allocations/3")
    text = page_text(response)
    assert response.status_code == 200
    assert "Asset Allocations for Will Smith" in text
    assert f"Domestic Stocks : {allocation['stocks']} %" in text
    assert f"Funds: {allocation['funds']} %" in text
    assert f"Bonds: {allocation['bonds']} %" in text


def test_missing_allocations_is_server_error(user1):
    response = user1.get("/allocations/999")
    assert response.status_code == 500
    assert "ERROR: No allocations found for the user" in page_text(response)
