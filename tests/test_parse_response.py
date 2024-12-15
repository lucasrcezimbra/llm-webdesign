from pathlib import Path
from types import GeneratorType

import pytest

from llm_webdesign.commands import parse


@pytest.fixture
def chunks():
    tests_dir = Path(__file__).parent
    with open(tests_dir  / 'chunks.txt', 'r') as f:
        chunks = f.readlines()
    return chunks


def test_parse_text():
    chunks = ["test"]
    code_chunks = []
    text_chunks = []

    parse(chunks, code_callback=code_chunks.append, text_callback=text_chunks.append)

    assert code_chunks == []
    assert text_chunks == ['test']


def test_parse_code():
    chunks = [
        "```\n",
        "code\n",
        "```"
    ]
    code_chunks = []
    text_chunks = []

    parse(chunks, code_callback=code_chunks.append, text_callback=text_chunks.append)

    assert code_chunks == ["code\n"]
    assert text_chunks == []


def test_parse_text_and_code():
    chunks = [
        "Text before code\n",
        "```\n",
        "code\n",
        "```\n",
        "Text after code"
    ]
    code_chunks = []
    text_chunks = []

    parse(chunks, code_callback=code_chunks.append, text_callback=text_chunks.append)

    assert code_chunks == ["code\n"]
    assert text_chunks == ["Text before code\n", "Text after code"]


@pytest.mark.skip("TODO")
def test_parse_code_with_languague():
    chunks = [
        "```",
        "python\n"
        "code\n",
        "```\n",
    ]
    code_chunks = []
    text_chunks = []

    parse(chunks, code_callback=code_chunks.append, text_callback=text_chunks.append)

    assert code_chunks == ["code\n"]
    assert text_chunks == []
