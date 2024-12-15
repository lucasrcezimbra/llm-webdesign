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


# TODO: improve prompt
# TODO: make customizable
SYSTEM_PROMPT = """
You are a Web Designer. You should prioritize the code (HTML, CSS, and JS) in your response.
"""
USER_PROMPT = """
Create a home page for my site. This is another page:
```html
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Missas</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="description"
              content="Plataforma que fornece informações sobre horários de missas e confissões em várias paróquias do Brasil, permitindo o filtro por dia e horários.">
        <meta name="keywords"
              content="missas, confissões, horários, paróquias, Brasil">
        <meta name="author" content="Lucas Rangel Cezimbra">

        <script src="/static/htmx.min.js" defer></script>
        <link href="/static/bootstrap.min.css" rel="stylesheet" async>
        <link rel="apple-touch-icon"
              sizes="180x180"
              href="/static/apple-touch-icon.png">
        <link rel="icon"
              type="image/png"
              sizes="32x32"
              href="/static/favicon-32x32.png">
        <link rel="icon"
              type="image/png"
              sizes="16x16"
              href="/static/favicon-16x16.png">
        <link rel="manifest" href="/static/site.webmanifest">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Open+Sans&display=swap"
              rel="stylesheet"
              async>
        <link href="/static/fontawesomefree/css/fontawesome.css"
              rel="stylesheet"
              type="text/css"
              async>
        <link href="/static/fontawesomefree/css/solid.css"
              rel="stylesheet"
              type="text/css"
              async>
        <link href="/static/fontawesomefree/css/brands.css"
              rel="stylesheet"
              type="text/css"
              async>
        <meta name="htmx-config" content='{"getCacheBusterParam":true}'>
        <style>
            body {
                background-color: #E1F5FE;
                font-family: 'Open Sans', sans-serif;
            }
            footer {
                background-color: #f8f9fa;
                padding: 1rem;
                text-align: center;
            }
            footer a {
                margin: 0 10px;
            }

    .my-indicator {
    display: none;
    }
    .htmx-request .my-indicator {
    display: block;
    }
    .inverse-indicator {
    display: block;
    }
    .htmx-request .inverse-indicator {
    display: none;
    }
    .form-range::-moz-range-track {
    background-color: #2a3142;
    }
    .verified {
    color: #2ecc71;
    }

        </style>
    </head>
    <body hx-boost="true">
        <div class="container mt-3">
            <div class="row mb-3 align-items-center">
                <div class="col-2 col-lg-1">
                    <img src="/static/logo.webp" style="max-width: 100%" loading="lazy">
                </div>
                <div class="col-10 col-lg-11">
                    <h1 class="fs-1">Missas.com.br</h1>
                </div>
            </div>
            <div class="row">
                <div class="col">
                    <nav aria-label="breadcrumb">
                        <ol class="breadcrumb">

                                <li class="breadcrumb-item">
                                    <a href="/rio-grande-do-norte">Rio Grande do Norte</a>
                                </li>
                                <li class="breadcrumb-item active" aria-current="page">Natal</li>

                        </ol>
                    </nav>
                </div>
            </div>
            <div id="content">


    <div class="row mb-3">
        <form hx-get="/rio-grande-do-norte/natal/"
              hx-indicator="#cards-indicator"
              hx-push-url="true"
              hx-target="#cards"
              hx-trigger="change">
            <div class="btn-group flex-wrap" role="group">
                <input class="btn-check"
                       id="missas"
                       name="tipo"
                       type="radio"
                       value="missas"
                       >
                <label class="btn btn-outline-primary rounded mx-1 my-1" for="missas">Missas</label>
                <input class="btn-check"
                       id="confissoes"
                       name="tipo"
                       type="radio"
                       value="confissoes"
                       checked>
                <label class="btn btn-outline-primary rounded mx-1 my-1" for="confissoes">Confissões</label>
            </div>
            <div class="vr"></div>
            <div class="btn-group flex-wrap" role="group">
                <input class="btn-check"
                       id="verified"
                       name="verificado"
                       type="checkbox"
                       value="1">
                <label class="btn btn-outline-primary rounded mx-1 my-1" for="verified">
                    <i class="fa-solid fa-circle-check verified"></i>
                </label>
            </div>
            <div class="vr"></div>
            <div class="btn-group flex-wrap" role="group">
                <input class="btn-check"
                       id="domingo"
                       name="dia"
                       type="radio"
                       value="domingo"
                       >
                <label class="btn btn-outline-primary rounded mx-1 my-1" for="domingo">Domingo</label>
                <input class="btn-check"
                       id="segunda"
                       name="dia"
                       type="radio"
                       value="segunda"
                       >
                <label class="btn btn-outline-primary rounded mx-1 my-1" for="segunda">2ª-feira</label>
                <input class="btn-check"
                       id="terca"
                       name="dia"
                       type="radio"
                       value="terca"
                       >
                <label class="btn btn-outline-primary rounded mx-1 my-1" for="terca">3ª-feira</label>
                <input class="btn-check"
                       id="quarta"
                       name="dia"
                       type="radio"
                       value="quarta"
                       >
                <label class="btn btn-outline-primary rounded mx-1 my-1" for="quarta">4ª-feira</label>
                <input class="btn-check"
                       id="quinta"
                       name="dia"
                       type="radio"
                       value="quinta"
                       >
                <label class="btn btn-outline-primary rounded mx-1 my-1" for="quinta">5ª-feira</label>
                <input class="btn-check"
                       id="sexta"
                       name="dia"
                       type="radio"
                       value="sexta"
                       checked>
                <label class="btn btn-outline-primary rounded mx-1 my-1" for="sexta">6ª-feira</label>
                <input class="btn-check"
                       id="sabado"
                       name="dia"
                       type="radio"
                       value="sabado"
                       >
                <label class="btn btn-outline-primary rounded mx-1 my-1" for="sabado">Sábado</label>
            </div>
            <div class="row">
                <div class="btn-group flex-wrap" role="group">
                    <label for="horario" class="form-label">
                        A partir das <span id="horarioValue">18</span> horas
                    </label>
                    <input class="form-range"
                           id="horario"
                           min="0"
                           max="23"
                           name="horario"
                           oninput="horarioValue.innerText = this.value"
                           type="range"
                           value="18">
                </div>
            </div>
        </form>
    </div>
    <div id="cards-indicator">

            <div class="card mb-3 my-indicator placeholder-glow">
                <div class="card-body">
                    <span class="fs-5 placeholder col-6"></span>
                    <div class="row">
                        <div class="col-6 col-md-2">
                            <span><i class="fa-solid fa-calendar-week"></i> <span class="placeholder col-6"></span></span>
                        </div>
                        <div class="col-6 col-md-2">
                            <span><i class="fa-solid fa-clock"></i> <span class="placeholder col-6"></span></span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card mb-3 my-indicator placeholder-glow">
                <div class="card-body">
                    <span class="fs-5 placeholder col-6"></span>
                    <div class="row">
                        <div class="col-6 col-md-2">
                            <span><i class="fa-solid fa-calendar-week"></i> <span class="placeholder col-6"></span></span>
                        </div>
                        <div class="col-6 col-md-2">
                            <span><i class="fa-solid fa-clock"></i> <span class="placeholder col-6"></span></span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card mb-3 my-indicator placeholder-glow">
                <div class="card-body">
                    <span class="fs-5 placeholder col-6"></span>
                    <div class="row">
                        <div class="col-6 col-md-2">
                            <span><i class="fa-solid fa-calendar-week"></i> <span class="placeholder col-6"></span></span>
                        </div>
                        <div class="col-6 col-md-2">
                            <span><i class="fa-solid fa-clock"></i> <span class="placeholder col-6"></span></span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card mb-3 my-indicator placeholder-glow">
                <div class="card-body">
                    <span class="fs-5 placeholder col-6"></span>
                    <div class="row">
                        <div class="col-6 col-md-2">
                            <span><i class="fa-solid fa-calendar-week"></i> <span class="placeholder col-6"></span></span>
                        </div>
                        <div class="col-6 col-md-2">
                            <span><i class="fa-solid fa-clock"></i> <span class="placeholder col-6"></span></span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card mb-3 my-indicator placeholder-glow">
                <div class="card-body">
                    <span class="fs-5 placeholder col-6"></span>
                    <div class="row">
                        <div class="col-6 col-md-2">
                            <span><i class="fa-solid fa-calendar-week"></i> <span class="placeholder col-6"></span></span>
                        </div>
                        <div class="col-6 col-md-2">
                            <span><i class="fa-solid fa-clock"></i> <span class="placeholder col-6"></span></span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card mb-3 my-indicator placeholder-glow">
                <div class="card-body">
                    <span class="fs-5 placeholder col-6"></span>
                    <div class="row">
                        <div class="col-6 col-md-2">
                            <span><i class="fa-solid fa-calendar-week"></i> <span class="placeholder col-6"></span></span>
                        </div>
                        <div class="col-6 col-md-2">
                            <span><i class="fa-solid fa-clock"></i> <span class="placeholder col-6"></span></span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card mb-3 my-indicator placeholder-glow">
                <div class="card-body">
                    <span class="fs-5 placeholder col-6"></span>
                    <div class="row">
                        <div class="col-6 col-md-2">
                            <span><i class="fa-solid fa-calendar-week"></i> <span class="placeholder col-6"></span></span>
                        </div>
                        <div class="col-6 col-md-2">
                            <span><i class="fa-solid fa-clock"></i> <span class="placeholder col-6"></span></span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card mb-3 my-indicator placeholder-glow">
                <div class="card-body">
                    <span class="fs-5 placeholder col-6"></span>
                    <div class="row">
                        <div class="col-6 col-md-2">
                            <span><i class="fa-solid fa-calendar-week"></i> <span class="placeholder col-6"></span></span>
                        </div>
                        <div class="col-6 col-md-2">
                            <span><i class="fa-solid fa-clock"></i> <span class="placeholder col-6"></span></span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card mb-3 my-indicator placeholder-glow">
                <div class="card-body">
                    <span class="fs-5 placeholder col-6"></span>
                    <div class="row">
                        <div class="col-6 col-md-2">
                            <span><i class="fa-solid fa-calendar-week"></i> <span class="placeholder col-6"></span></span>
                        </div>
                        <div class="col-6 col-md-2">
                            <span><i class="fa-solid fa-clock"></i> <span class="placeholder col-6"></span></span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card mb-3 my-indicator placeholder-glow">
                <div class="card-body">
                    <span class="fs-5 placeholder col-6"></span>
                    <div class="row">
                        <div class="col-6 col-md-2">
                            <span><i class="fa-solid fa-calendar-week"></i> <span class="placeholder col-6"></span></span>
                        </div>
                        <div class="col-6 col-md-2">
                            <span><i class="fa-solid fa-clock"></i> <span class="placeholder col-6"></span></span>
                        </div>
                    </div>
                </div>
            </div>

        <div id="cards">

        <div class="card mb-3 inverse-indicator">
            <div class="card-body">
                <span class="fs-5">Paróquia do Bom Jesus das Dores</span>

                <div class="row">
                    <div class="col-auto">
                        <span><i class="fa-solid fa-calendar-week"></i> Sexta-feira</span>
                    </div>
                    <div class="col-auto">
                        <span>
                            <i class="fa-solid fa-clock"></i>
                            16:30
                            - 18:00
                        </span>
                    </div>

                </div>
                <div class="row">

                        <div class="col-auto">
                            <i class="fa-solid fa-circle-check verified"></i>
                            Verificado por Missas.com.br em 20/05/2024
                        </div>

                    <div class="col-auto">
                        <span>
                            <i class="fa-solid fa-exclamation-circle"></i>

                                Fonte: <a href="https://www.arquidiocesedenatal.org.br/c%C3%B3pia-hor%C3%A1rios-de-missa-2" target="_blank">Arquidiocese de Natal</a>

                        </span>
                    </div>
                </div>
            </div>
        </div>

</div>

    </div>


            </div>
        </div>
        <footer>
            <a href="/">Início</a> |
            <a href="https://github.com/lucasrcezimbra/missas.com.br"
               target="_blank">
                <i class="fa-solid fa-brands fa-github"></i> GitHub
            </a>
        </footer>
        <script src="/static/bootstrap.min.js" defer></script>
        <script defer
                src='https://static.cloudflareinsights.com/beacon.min.js'
                data-cf-beacon='{"token": "b300d389869f4fac95d6c34ac8ea2d0d"}'></script>
    </body>
</html>
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
    @click.argument("args", nargs=-1, type=click.UNPROCESSED)
    def webdesign(args):
        """
        TODO: Run IPython interpreter, passing through any arguments
        """
        temp_dir = tempfile.mkdtemp()
        start_server(temp_dir)
        assert webbrowser.open(f"http://localhost:{PORT}")

        model = llm.get_model(get_default_model())
        if model.needs_key:
            model.key = llm.get_key(None, model.needs_key, model.key_env_var)

        # TODO: read user prompt from user
        response = model.prompt(USER_PROMPT, system=SYSTEM_PROMPT)

        filepath = f"{temp_dir}/index.html"  # TODO: use pathlib

        with open(filepath, "w") as f:
            f.write("")

        my_print = partial(print, end="")

        with open(filepath, "a") as f:
            my_write = partial(write, f)
            parse(response, my_print, my_write)

        input("x")
