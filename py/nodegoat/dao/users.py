"""Port of app/data/user-dao.js.

Deliberate quirks are tagged ``# PARITY: <ID>``; see PARITY_REGISTER.md.
"""

import math
import random
from datetime import datetime
from typing import Any

from pymongo import ReturnDocument
from pymongo.database import Database

from nodegoat import jscompat


class InvalidPasswordError(Exception):
    invalid_password = True

    def __init__(self) -> None:
        super().__init__("Invalid password")


class NoSuchUserError(Exception):
    no_such_user = True

    def __init__(self) -> None:
        super().__init__("User: null does not exist")  # PARITY: P-004


class UserDAO:
    def __init__(self, db: Database) -> None:
        self._db = db
        self._users = db["users"]

    def add_user(
        self, user_name: Any, first_name: Any, last_name: Any, password: Any, email: Any = None
    ) -> dict[str, Any]:
        user = {
            "userName": user_name,
            "firstName": first_name,
            "lastName": last_name,
            "benefitStartDate": self.get_random_future_date(),
            "password": password,  # PARITY: P-001
        }
        if jscompat.truthy(email):  # PARITY: P-010
            user["email"] = email
        user["_id"] = self.get_next_sequence("userId")  # PARITY: P-008
        self._users.insert_one(user)  # PARITY: P-011
        return user

    def get_random_future_date(self) -> str:
        # PARITY: P-009
        today = datetime.now()
        day = (math.floor(random.random() * 10) + today.isoweekday() % 7) % 29
        month = (math.floor(random.random() * 10) + today.month - 1) % 12
        year = math.ceil(random.random() * 30) + today.year
        return f"{year}-{month:02d}-{day:02d}"

    def validate_login(self, user_name: Any, password: Any) -> dict[str, Any]:
        user = self._users.find_one({"userName": user_name})  # PARITY: P-005
        if user is None:
            raise NoSuchUserError()  # PARITY: P-003
        if not jscompat.strict_equals(password, user.get("password")):  # PARITY: P-002
            raise InvalidPasswordError()  # PARITY: P-003
        return user

    def get_user_by_id(self, user_id: Any) -> dict[str, Any] | None:
        return self._users.find_one({"_id": jscompat.parse_int(user_id)})  # PARITY: P-006

    def get_user_by_user_name(self, user_name: Any) -> dict[str, Any] | None:
        return self._users.find_one({"userName": user_name})  # PARITY: P-005

    def get_next_sequence(self, name: Any) -> Any:
        data = self._db["counters"].find_one_and_update(
            {"_id": name}, {"$inc": {"seq": 1}}, return_document=ReturnDocument.AFTER
        )
        seq = data["seq"]  # PARITY: P-007
        return int(seq) if isinstance(seq, float) and seq.is_integer() else seq  # PARITY: P-008
