from pymongo import MongoClient
from pymongo.database import Database


def connect(mongodb_uri: str) -> MongoClient:
    client = MongoClient(mongodb_uri)
    try:
        client.admin.command("ping")
    except Exception:
        client.close()
        raise
    return client


def default_database(client: MongoClient) -> Database:
    return client.get_default_database(default="admin")
