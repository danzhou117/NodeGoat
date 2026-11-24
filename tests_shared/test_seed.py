from bson import ObjectId

from helpers import SEED_USERS


def test_seed_matches_expected_documents(db):
    users = list(db.users.find().sort("_id", 1))
    assert users == SEED_USERS
    assert all(type(user["_id"]) is int for user in users)

    assert list(db.counters.find()) == [{"_id": "userId", "seq": 3}]
    assert type(db.counters.find_one({"_id": "userId"})["seq"]) is int

    allocations = list(db.allocations.find())
    assert len(allocations) == 3
    assert {allocation["userId"] for allocation in allocations} == {1, 2, 3}
    for allocation in allocations:
        assert set(allocation) == {"_id", "userId", "stocks", "funds", "bonds"}
        assert type(allocation["_id"]) is ObjectId
        assert type(allocation["userId"]) is int
        assert type(allocation["stocks"]) is int
        assert type(allocation["funds"]) is int
        assert type(allocation["bonds"]) is int
        assert 1 <= allocation["stocks"] <= 40
        assert 1 <= allocation["funds"] <= 40
        assert allocation["bonds"] == 100 - allocation["stocks"] - allocation["funds"]

    assert db.contributions.count_documents({}) == 0
    assert db.memos.count_documents({}) == 0
