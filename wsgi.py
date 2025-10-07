# wsgi.py  —  Flask entrypoint for Render / Gunicorn

try:
    # If your app file is named app.py and defines "app = Flask(__name__)"
    from app import app
except ImportError:
    # fallback if your main file is named differently (e.g. main.py)
    from main import app

# Optional: health-check route (helps Render verify the service)
if not any(rule.rule == "/healthz" for rule in app.url_map.iter_rules()):
    @app.get("/healthz")
    def healthz():
        return {"ok": True}, 200
