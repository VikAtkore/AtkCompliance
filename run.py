import os

# Load .env before the app factory reads configuration. Optional dependency --
# `flask run` loads .env on its own, this covers `python run.py` too.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app import create_app  # noqa: E402

app = create_app(os.environ.get("ACC_ENV"))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("ACC_PORT", 5000)), debug=True)
