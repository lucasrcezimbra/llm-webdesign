from textwrap import dedent

from llm_webdesign import format_prompt


def test_format_prompt():
    user_prompt = "Create a cool home page"
    file_content = dedent(
        """\
        <html>
        <body>
        </body>"""
    )

    prompt = format_prompt(user_prompt, file_content)

    assert prompt == dedent(
        """\
        Create a cool home page

        ```
        <html>
        <body>
        </body>
        ```"""
    )
