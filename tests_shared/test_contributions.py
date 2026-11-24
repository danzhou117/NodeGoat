import pytest

from helpers import page_text


def test_contribution_defaults(user1, db):
    response = user1.get("/contributions")
    text = page_text(response)
    assert response.status_code == 200
    assert "Payroll Contribution Percent" in text
    assert "Employee Pre-Tax 2 %" in text
    assert "Roth Contribution 2 %" in text
    assert "Employee After Tax 2 %" in text
    assert db.contributions.count_documents({}) == 0


@pytest.mark.parametrize("values", [(5, 3, 2), (10, 10, 10)])
def test_valid_contribution_update(values, user1, db):
    pre_tax, after_tax, roth = values
    response = user1.post(
        "/contributions",
        data={"preTax": str(pre_tax), "afterTax": str(after_tax), "roth": str(roth)},
    )
    text = page_text(response)
    assert response.status_code == 200
    assert "Contributions updated successfully." in text
    assert f"Employee Pre-Tax {pre_tax} %" in text
    assert f"Employee After Tax {after_tax} %" in text
    assert f"Roth Contribution {roth} %" in text
    contribution = db.contributions.find_one({"userId": 2})
    assert set(contribution) == {"_id", "userId", "preTax", "afterTax", "roth"}
    assert type(contribution["userId"]) is int
    assert type(contribution["preTax"]) is int
    assert type(contribution["afterTax"]) is int
    assert type(contribution["roth"]) is int
    assert contribution["userId"] == 2
    assert contribution["preTax"] == pre_tax
    assert contribution["afterTax"] == after_tax
    assert contribution["roth"] == roth
    assert db.contributions.count_documents({"userId": 2}) == 1
    stored = user1.get("/contributions")
    assert f"Employee Pre-Tax {pre_tax} %" in page_text(stored)
    assert f"Employee After Tax {after_tax} %" in page_text(stored)
    assert f"Roth Contribution {roth} %" in page_text(stored)


def test_second_contribution_update_replaces_first(user1, db):
    response = user1.post(
        "/contributions",
        data={"preTax": "5", "afterTax": "3", "roth": "2"},
    )
    assert response.status_code == 200
    assert "Contributions updated successfully." in page_text(response)
    first = db.contributions.find_one({"userId": 2})
    assert set(first) == {"_id", "userId", "preTax", "afterTax", "roth"}
    assert type(first["userId"]) is int
    assert type(first["preTax"]) is int
    assert type(first["afterTax"]) is int
    assert type(first["roth"]) is int
    assert first["userId"] == 2
    assert first["preTax"] == 5
    assert first["afterTax"] == 3
    assert first["roth"] == 2
    assert db.contributions.count_documents({"userId": 2}) == 1
    response = user1.post(
        "/contributions",
        data={"preTax": "10", "afterTax": "10", "roth": "10"},
    )
    assert response.status_code == 200
    assert "Contributions updated successfully." in page_text(response)
    contribution = db.contributions.find_one({"userId": 2})
    assert set(contribution) == {"_id", "userId", "preTax", "afterTax", "roth"}
    assert type(contribution["userId"]) is int
    assert type(contribution["preTax"]) is int
    assert type(contribution["afterTax"]) is int
    assert type(contribution["roth"]) is int
    assert contribution["userId"] == 2
    assert contribution["preTax"] == 10
    assert contribution["afterTax"] == 10
    assert contribution["roth"] == 10
    assert db.contributions.count_documents({"userId": 2}) == 1


@pytest.mark.parametrize(
    "data",
    [
        {"preTax": "-1", "afterTax": "3", "roth": "2"},
        {"preTax": "", "afterTax": "3", "roth": "2"},
    ],
)
def test_invalid_contribution_values(data, user1, db):
    response = user1.post("/contributions", data=data)
    text = page_text(response)
    assert response.status_code == 200
    assert "Invalid contribution percentages" in text
    assert "Contributions updated successfully." not in text
    assert db.contributions.count_documents({}) == 0


def test_contribution_total_over_thirty_is_rejected(user1, db):
    response = user1.post(
        "/contributions",
        data={"preTax": "10", "afterTax": "11", "roth": "10"},
    )
    assert response.status_code == 200
    assert "Contribution percentages cannot exceed 30 %" in page_text(response)
    assert db.contributions.count_documents({}) == 0


def test_contribution_eval_is_pinned(user1, db):
    """Pins the insecure eval behavior in contribution inputs."""
    response = user1.post(
        "/contributions",
        data={"preTax": "2+3", "afterTax": "1", "roth": "1"},
    )
    assert response.status_code == 200
    assert "Contributions updated successfully." in page_text(response)
    contribution = db.contributions.find_one({"userId": 2})
    assert set(contribution) == {"_id", "userId", "preTax", "afterTax", "roth"}
    assert type(contribution["preTax"]) is int
    assert type(contribution["afterTax"]) is int
    assert type(contribution["roth"]) is int
    assert contribution["preTax"] == 5
    assert contribution["afterTax"] == 1
    assert contribution["roth"] == 1


def test_non_numeric_contribution_is_server_error(user1, db):
    """Pins the server error caused by evaluating non-numeric input."""
    response = user1.post(
        "/contributions",
        data={"preTax": "abc", "afterTax": "1", "roth": "1"},
    )
    assert response.status_code == 500
    assert "Oops.." in page_text(response)
    assert db.contributions.count_documents({}) == 0
