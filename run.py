import os
from app import create_app

app = create_app(os.environ.get("ACC_ENV"))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("ACC_PORT", 5000)))
