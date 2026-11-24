import pytest

from helpers import ADMIN, SEED_USERS, USER1, page_text


def test_login_page(anon):
    response = anon.get("/login")
    assert response.status_code == 200
    assert "New user? Sign Up" in page_text(response)


def test_user_login_redirects_to_dashboard(anon, db):
    response = anon.post("/login", data={"userName": USER1[0], "password": USER1[1]})
    assert response.status_code == 302
    assert response.headers["location"] == "/dashboard"

    dashboard = anon.get("/dashboard")
    assert dashboard.status_code == 200
    assert "Total Retirement Savings" in page_text(dashboard)
    assert "John Doe" in page_text(dashboard)

    root = anon.get("/")
    assert root.status_code == 200
    assert "Total Retirement Savings" in page_text(root)
    assert "John Doe" in page_text(root)
    assert list(db.users.find().sort("_id", 1)) == SEED_USERS


def test_admin_login_redirects_to_benefits(anon):
    response = anon.post("/login", data={"userName": ADMIN[0], "password": ADMIN[1]})
    assert response.status_code == 302
    assert response.headers["location"] == "/benefits"

    benefits = anon.get("/benefits")
    assert benefits.status_code == 200
    assert "Benefits Start Date" in page_text(benefits)


def test_bad_username_is_echoed_and_distinguished(anon, db):
    """Pins the user-enumeration behavior in the login errors."""
    response = anon.post(
        "/login",
        data={"userName": "nosuchuser", "password": "User1_123"},
    )
    text = page_text(response)
    assert response.status_code == 200
    assert "Invalid username" in text
    assert "Invalid password" not in text
    assert "New user? Sign Up" in text
    assert "nosuchuser" in response.text
    dashboard = anon.get("/dashboard")
    assert dashboard.status_code == 302
    assert dashboard.headers["location"] == "/login"
    assert list(db.users.find().sort("_id", 1)) == SEED_USERS


def test_bad_password_is_distinguished(anon, db):
    """Pins the user-enumeration behavior in the login errors."""
    response = anon.post(
        "/login",
        data={"userName": "user1", "password": "wrong"},
    )
    text = page_text(response)
    assert response.status_code == 200
    assert "Invalid password" in text
    assert "Invalid username" not in text
    assert "New user? Sign Up" in text
    dashboard = anon.get("/dashboard")
    assert dashboard.status_code == 302
    assert dashboard.headers["location"] == "/login"
    assert list(db.users.find().sort("_id", 1)) == SEED_USERS


def test_logout_redirects_and_removes_session(user1, anon):
    response = user1.get("/logout")
    assert response.status_code == 302
    assert response.headers["location"] == "/"
    for path in ("/dashboard", "/"):
        after_logout = user1.get(path)
        assert after_logout.status_code == 302
        assert after_logout.headers["location"] == "/login"
    response = anon.get("/logout")
    assert response.status_code == 302
    assert response.headers["location"] == "/"


@pytest.mark.parametrize(
    "path",
    ["/", "/dashboard", "/profile", "/contributions", "/benefits", "/allocations/2", "/memos"],
)
def test_anonymous_gets_are_guarded(anon, path):
    response = anon.get(path)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


@pytest.mark.parametrize(
    ("path", "data"),
    [
        (
            "/profile",
            {
                "firstName": "John",
                "lastName": "Doe",
                "ssn": "123-45-6789",
                "dob": "1990-01-15",
                "address": "1 Main St",
                "bankAcc": "12345678",
                "bankRouting": "0198212#",
            },
        ),
        ("/contributions", {"preTax": "5", "afterTax": "3", "roth": "2"}),
        ("/benefits", {"userId": "2", "benefitStartDate": "2031-05-20"}),
        ("/memos", {"memo": "unauthorized"}),
    ],
)
def test_anonymous_posts_are_guarded_and_do_not_write(anon, db, path, data):
    response = anon.post(path, data=data)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"
    assert list(db.users.find().sort("_id", 1)) == SEED_USERS
    assert db.contributions.count_documents({}) == 0
    assert db.memos.count_documents({}) == 0
