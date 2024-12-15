import http.server
import os
import socketserver
import tempfile
import threading
import webbrowser
from functools import partial

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
USER_PROMPT = """
Create a home page for my site. This is another page:
```html
{html}
```
"""

PORT = 9873  # TODO: receive as CLI arg


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


def parse(chunks, text_callback, code_callback):
    code = False
    for chunk in chunks:
        if "```" in chunk:
            # TODO: fix this for cases when the chunk contains more than ```
            code = not code
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
        temp_dir = tempfile.mkdtemp()
        start_server(temp_dir)
        assert webbrowser.open(f"http://localhost:{PORT}")

        model = llm.get_model(get_default_model())
        if model.needs_key:
            model.key = llm.get_key(None, model.needs_key, model.key_env_var)

        # TODO: read all files
        # TODO: use pathlib
        with open(f"{path}/index.html") as f:
            index_content = f.read()

        # TODO: read user prompt from user
        response = model.prompt(
            USER_PROMPT.format(html=index_content), system=SYSTEM_PROMPT
        )

        filepath = f"{temp_dir}/index.html"  # TODO: use pathlib

        with open(filepath, "w") as f:
            f.write("")

        my_print = partial(print, end="")

        with open(filepath, "a") as f:
            my_write = partial(write, f)
            parse(response, my_print, my_write)

        input("Press Enter to finish.")
