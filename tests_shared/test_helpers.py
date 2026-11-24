import httpx

from helpers import page_text


def test_page_text_separates_block_elements_without_template_whitespace():
    response = httpx.Response(
        200,
        text="<table><tr><td>2</td><td>John</td><td>Doe</td></tr></table>"
        "<p>Retire<b>Easy</b></p><script>var hidden = 1;</script>",
    )
    assert page_text(response) == "2 John Doe RetireEasy"
