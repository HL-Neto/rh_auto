
import threading
import webbrowser
import logging

from API.api import app

logging.basicConfig(level=logging.DEBUG)


def abrir_navegador():
    webbrowser.open("http://127.0.0.1:2000")


if __name__ == "__main__":
    threading.Timer(1.5, abrir_navegador).start()

    app.run(
        host="127.0.0.1",
        port=2000,
        debug=False,
        use_reloader=False
    )
