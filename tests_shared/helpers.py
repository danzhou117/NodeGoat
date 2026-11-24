import time
from html.parser import HTMLParser
import re


USER1 = ("user1", "User1_123")
USER2 = ("user2", "User2_123")
ADMIN = ("admin", "Admin_123")

SEED_USERS = [
    {
        "_id": 1,
        "userName": "admin",
        "firstName": "Node Goat",
        "lastName": "Admin",
        "password": "Admin_123",
        "isAdmin": True,
    },
    {
        "_id": 2,
        "userName": "user1",
        "firstName": "John",
        "lastName": "Doe",
        "benefitStartDate": "2030-01-10",
        "password": "User1_123",
    },
    {
        "_id": 3,
        "userName": "user2",
        "firstName": "Will",
        "lastName": "Smith",
        "benefitStartDate": "2025-11-30",
        "password": "User2_123",
    },
]

_INLINE_TAGS = {
    "a", "abbr", "b", "bdi", "bdo", "cite", "code", "dfn", "em", "i", "kbd", "label",
    "mark", "q", "s", "samp", "small", "span", "strong", "sub", "sup", "time", "u", "var",
}


class _VisibleTextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.ignored_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.ignored_depth += 1
        elif tag not in _INLINE_TAGS:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.ignored_depth:
            self.ignored_depth -= 1
        elif tag not in _INLINE_TAGS:
            self.parts.append(" ")

    def handle_data(self, data):
        if not self.ignored_depth:
            self.parts.append(data)


def page_text(response) -> str:
    parser = _VisibleTextParser()
    parser.feed(response.text)
    parser.close()
    return re.sub(r"\s+", " ", "".join(parser.parts)).strip()


def wait_for(predicate, timeout=5.0, interval=0.05):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(interval)
    raise AssertionError("predicate did not become truthy before timeout")
