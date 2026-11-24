import datetime
import time

from bson import ObjectId

from helpers import page_text


def test_memos_page_is_empty(user1, db):
    response = user1.get("/memos")
    assert response.status_code == 200
    assert "Send a memo" in page_text(response)
    assert db.memos.count_documents({}) == 0


def test_add_memo_renders_and_stores_raw_markdown(user1, db):
    memo = "Shared suite memo **bold**"
    started = datetime.datetime.now(datetime.timezone.utc)
    response = user1.post("/memos", data={"memo": memo})
    ended = datetime.datetime.now(datetime.timezone.utc)
    assert response.status_code == 200
    assert "Shared suite memo bold" in page_text(response)
    assert "<strong>bold</strong>" in response.text
    stored = list(db.memos.find())
    assert len(stored) == 1
    document = stored[0]
    assert set(document) == {"_id", "memo", "timestamp"}
    assert type(document["_id"]) is ObjectId
    assert type(document["memo"]) is str
    assert document["memo"] == memo
    assert isinstance(document["timestamp"], datetime.datetime)
    assert document["timestamp"].tzinfo is not None
    assert started - datetime.timedelta(seconds=60) <= document["timestamp"] <= ended + datetime.timedelta(seconds=60)


def test_memos_are_newest_first(user1, db):
    response = user1.post("/memos", data={"memo": "first memo"})
    assert response.status_code == 200
    assert "first memo" in page_text(response)
    first = list(db.memos.find())
    assert len(first) == 1
    assert set(first[0]) == {"_id", "memo", "timestamp"}
    assert type(first[0]["_id"]) is ObjectId
    assert type(first[0]["memo"]) is str
    assert first[0]["memo"] == "first memo"
    assert isinstance(first[0]["timestamp"], datetime.datetime)
    time.sleep(0.05)
    response = user1.post("/memos", data={"memo": "second memo"})
    assert response.status_code == 200
    assert "second memo" in page_text(response)
    second = list(db.memos.find({"memo": "second memo"}))
    assert len(second) == 1
    assert set(second[0]) == {"_id", "memo", "timestamp"}
    assert type(second[0]["_id"]) is ObjectId
    assert type(second[0]["memo"]) is str
    assert second[0]["memo"] == "second memo"
    assert isinstance(second[0]["timestamp"], datetime.datetime)
    text = page_text(user1.get("/memos"))
    assert text.index("second memo") < text.index("first memo")
    documents = list(db.memos.find().sort("timestamp", 1))
    assert len(documents) == 2
    assert documents[0]["timestamp"] < documents[1]["timestamp"]


def test_memos_are_global(user1, user2, db):
    response = user1.post("/memos", data={"memo": "global memo"})
    assert response.status_code == 200
    assert "global memo" in page_text(response)
    stored = db.memos.find_one({"memo": "global memo"})
    assert set(stored) == {"_id", "memo", "timestamp"}
    assert type(stored["_id"]) is ObjectId
    assert type(stored["memo"]) is str
    assert stored["memo"] == "global memo"
    assert isinstance(stored["timestamp"], datetime.datetime)
    assert db.memos.count_documents({}) == 1
    response = user2.get("/memos")
    assert response.status_code == 200
    assert "global memo" in page_text(response)
