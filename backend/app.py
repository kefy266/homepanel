import io
import os
import secrets
import time
import uuid
from pathlib import Path
from functools import wraps

import qrcode
from flask import Flask, jsonify, redirect, render_template, request, session, send_file, abort, url_for
from werkzeug.utils import secure_filename

from system_monitor import collect_stats

APP_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", "/srv/homepanel/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
if not ADMIN_PASSWORD:
    raise RuntimeError("ADMIN_PASSWORD is missing. Configure /etc/homepanel.env")

app = Flask(__name__, template_folder=str(APP_DIR / "frontend"), static_folder=str(APP_DIR / "frontend" / "static"))
app.secret_key = os.environ.get("FLASK_SECRET", secrets.token_hex(32))
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("COOKIE_SECURE", "0") == "1"

# In-memory, short-lived, single-use transfer tokens.
transfer_tokens = {}
TOKEN_TTL = 600

def authenticated():
    return session.get("authenticated") is True

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not authenticated():
            if request.path.startswith("/api/"):
                return jsonify(error="authentication_required"), 401
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapped

@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=()"
    response.headers["Cache-Control"] = "no-store"
    return response

@app.get("/login")
def login():
    if authenticated():
        return redirect(url_for("dashboard"))
    return render_template("login.html", error=None)

@app.post("/login")
def login_post():
    supplied = request.form.get("password", "")
    if secrets.compare_digest(supplied, ADMIN_PASSWORD):
        session.clear()
        session["authenticated"] = True
        return redirect(url_for("dashboard"))
    return render_template("login.html", error="Şifre yanlış. Tekrar dene."), 401

@app.post("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.get("/")
@login_required
def dashboard():
    return render_template("index.html")

@app.get("/api/stats")
@login_required
def stats():
    return jsonify(collect_stats())

@app.post("/api/transfer/new")
@login_required
def new_transfer():
    now = time.time()
    # Prune expired links.
    for token, data in list(transfer_tokens.items()):
        if data["expires"] <= now:
            transfer_tokens.pop(token, None)
    token = secrets.token_urlsafe(24)
    transfer_tokens[token] = {"expires": now + TOKEN_TTL}
    upload_url = request.host_url.rstrip("/") + url_for("upload_page", token=token)
    return jsonify(url=upload_url, expires_in=TOKEN_TTL)

@app.get("/api/transfer/qr/<token>.png")
@login_required
def transfer_qr(token):
    data = transfer_tokens.get(token)
    if not data or data["expires"] <= time.time():
        transfer_tokens.pop(token, None)
        abort(404)
    img = qrcode.make(request.host_url.rstrip("/") + url_for("upload_page", token=token))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

@app.get("/upload/<token>")
def upload_page(token):
    data = transfer_tokens.get(token)
    if not data or data["expires"] <= time.time():
        transfer_tokens.pop(token, None)
        return render_template("upload.html", invalid=True), 404
    return render_template("upload.html", invalid=False, token=token)

@app.post("/upload/<token>")
def upload_file(token):
    data = transfer_tokens.get(token)
    if not data or data["expires"] <= time.time():
        transfer_tokens.pop(token, None)
        return "Bu aktarım bağlantısının süresi dolmuş.", 410
    incoming = request.files.get("file")
    if not incoming or not incoming.filename:
        return "Dosya seçilmedi.", 400
    original = secure_filename(incoming.filename) or "upload"
    suffix = Path(original).suffix[:20]
    stored = f"{uuid.uuid4().hex}{suffix}"
    incoming.save(UPLOAD_DIR / stored)
    transfer_tokens.pop(token, None)
    return render_template("upload.html", success=True, filename=original)

@app.errorhandler(413)
def too_large(_):
    return "Dosya boyutu 100 MB sınırını aşıyor.", 413

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8787")))
