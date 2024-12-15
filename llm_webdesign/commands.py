import http.server
import os
import socketserver
import tempfile
import threading
import webbrowser
from functools import partial
from pathlib import Path

import click
import llm
from llm.cli import get_default_model

# TODO: start from a URL e.g. --url=https://missas.com.br/ downloads the code
#       and save to the temp folder
# TODO: --path to pass a dir to read the files from, then copy the files to /tmp
#       by default and edit there.
# TODO: read the files in the dir and send to the LLM
# TODO: in-place flag to edit in the directory instead of creating a temp dir.
#       can't be used with --url
# TODO: chat


# TODO: improve prompt
# TODO: make customizable
SYSTEM_PROMPT = """
You are a Web Designer. You should prioritize the code (HTML, CSS, and JS) in your response.
"""
PORT = 9876  # TODO: receive as CLI arg
CODE_DELIMITER = "```"


def run_server(directory):
    os.chdir(directory)
    Handler = http.server.SimpleHTTPRequestHandler
    # TODO: parametrize host
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()


def start_server(directory):
    # TODO: kill after finishing script
    server_thread = threading.Thread(target=run_server, args=(directory,))
    server_thread.daemon = True
    server_thread.start()


def parse(chunks, text_callback, code_callback, code_delimiter=CODE_DELIMITER):
    # TODO: refactor this crazy logic
    code = False
    current_line = ""
    for chunk in chunks:
        if current_line.endswith("\n"):
            # TODO: remove hard coded `
            if code and "`" in current_line and code_delimiter not in current_line:
                code_callback(current_line)
            current_line = ""
        current_line += chunk
        if code_delimiter in chunk or code_delimiter in current_line:
            # TODO: fix this for cases when the chunk contains more than ```
            code = not code
            continue
        if "`" in current_line:
            continue

        callback = code_callback if code else text_callback
        callback(chunk)


def write(f, chunk):
    f.write(chunk)
    f.flush()


@llm.hookimpl
def register_commands(cli):
    @cli.command(context_settings={"ignore_unknown_options": True})
    @click.option("--path", help="Path to the directory with the files")
    @click.argument("args", nargs=-1, type=click.UNPROCESSED)
    def webdesign(args, path):
        """
        TODO: Run IPython interpreter, passing through any arguments
        """
        path = Path(path)
        temp_dir = Path(tempfile.mkdtemp())
        start_server(temp_dir)
        assert webbrowser.open(f"http://localhost:{PORT}")

        model = llm.get_model(get_default_model())
        if model.needs_key:
            model.key = llm.get_key(None, model.needs_key, model.key_env_var)

        # TODO: read all files
        with open(path / "index.html") as f:
            index_content = f.read()

        prompt = "".join(args)
        response = model.prompt(prompt.format(html=index_content), system=SYSTEM_PROMPT)

        filepath = temp_dir / "index.html"

        with open(filepath, "w") as f:
            f.write("")

        my_print = partial(print, end="")

        with open(filepath, "a") as f:
            my_write = partial(write, f)
            parse(response, my_print, my_write)

        input("Press Enter to finish.")
