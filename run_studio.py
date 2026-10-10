#!/usr/bin/env python3
"""
Unified Server for Media Studio, Remember, Effects Studio, and ZoomPan Studio
Serves all applications on a single port (5200).
"""

import os
import re
import signal
import sys
import importlib.util
import matplotlib
matplotlib.use("Agg")
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

print("=================================================================", flush=True)
print("🚀 Media Studio Unified Server Starting", flush=True)
print("   Loading modules (takes 1-3 minutes on older hardware)...", flush=True)
print("=================================================================", flush=True)

# Import base applications
print("[1/5] Loading Media Studio & AI models...", flush=True)
import MediaStudioSD2
print("      Media Studio loaded.", flush=True)

print("[2/5] Loading Remember DB...", flush=True)
import remember
print("      Remember DB loaded.", flush=True)

print("[3/5] Loading Effects Studio...", flush=True)
from effects_studio.app import app as effects_app
print("      Effects Studio loaded.", flush=True)

print("[4/5] Loading ZoomPan Studio...", flush=True)
# Dynamically import ZOOM-PAN app (folder contains hyphen)
zoompan_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ZOOM-PAN")
zoompan_app_path = os.path.join(zoompan_dir, "app.py")
zoompan_spec = importlib.util.spec_from_file_location("zoompan_app", zoompan_app_path)
zoompan_module = importlib.util.module_from_spec(zoompan_spec)
sys.modules["zoompan_app"] = zoompan_module
zoompan_spec.loader.exec_module(zoompan_module)
zoompan_app = zoompan_module.app
print("      ZoomPan Studio loaded.", flush=True)

# Configure ZoomPan directories & session
zoompan_app.root_path = zoompan_dir
zoompan_app.static_folder = os.path.join(zoompan_dir, "static")
zoompan_app.template_folder = os.path.join(zoompan_dir, "templates")
zoompan_app.config["TEMPLATES_AUTO_RELOAD"] = True
zoompan_app.config["SESSION_COOKIE_NAME"] = "zoompan_session"
zoompan_app.config["SESSION_COOKIE_PATH"] = "/zoompan"

print("[5/6] Loading SciFi Vision Studio...", flush=True)
scifi_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scifi-writer_1")
if scifi_dir not in sys.path:
    sys.path.insert(0, scifi_dir)
scifi_app_path = os.path.join(scifi_dir, "app.py")
scifi_spec = importlib.util.spec_from_file_location("scifi_app_module", scifi_app_path)
scifi_module = importlib.util.module_from_spec(scifi_spec)
sys.modules["scifi_app_module"] = scifi_module
scifi_spec.loader.exec_module(scifi_module)
scifi_app = scifi_module.app
print("      SciFi Vision Studio loaded.", flush=True)

# Configure SciFi directories & session
scifi_app.root_path = scifi_dir
scifi_app.static_folder = os.path.join(scifi_dir, "static")
scifi_app.template_folder = os.path.join(scifi_dir, "templates")
scifi_app.config["TEMPLATES_AUTO_RELOAD"] = True
scifi_app.config["SESSION_COOKIE_NAME"] = "scifi_session"
scifi_app.config["SESSION_COOKIE_PATH"] = "/scifi"

print("[6/6] Loading AI Codebase & LoRA Studio...", flush=True)
from flask_chat_codebase import app as chat_app
chat_app.config["TEMPLATES_AUTO_RELOAD"] = True
chat_app.config["SESSION_COOKIE_NAME"] = "chat_session"
chat_app.config["SESSION_COOKIE_PATH"] = "/chat"
print("      AI Codebase & LoRA Studio loaded.", flush=True)

# Enable automatic template reloading for all apps
MediaStudioSD2.app.config["TEMPLATES_AUTO_RELOAD"] = True
remember.app.config["TEMPLATES_AUTO_RELOAD"] = True
effects_app.config["TEMPLATES_AUTO_RELOAD"] = True

# Initialize Media Studio databases & text files
MediaStudioSD2.create_caption_db()
MediaStudioSD2.init_db()
MediaStudioSD2.start_gc_monitor()
MediaStudioSD2.load_txt_files("static/TEXT")

# Initialize Remember database
remember.init_db()

# Isolate session cookies so applications don't conflict
remember.app.config["SESSION_COOKIE_NAME"] = "remember_session"
remember.app.config["SESSION_COOKIE_PATH"] = "/remember"
effects_app.config["SESSION_COOKIE_NAME"] = "effects_session"
effects_app.config["SESSION_COOKIE_PATH"] = "/effects"

# Ensure Remember's CSS route works globally
@MediaStudioSD2.app.route("/_ui_css/<name>.css")
def remember_css_fallback(name):
    return remember.ui_css(name)

# Ensure /effects_studio redirects to /effects
@MediaStudioSD2.app.route("/effects_studio")
@MediaStudioSD2.app.route("/effects_studio/")
def effects_studio_alias():
    from flask import redirect
    return redirect("/effects")

# Ensure /zoompan and aliases redirect to /zoompan/
@MediaStudioSD2.app.route("/zoompan")
@MediaStudioSD2.app.route("/zoom_pan")
@MediaStudioSD2.app.route("/zoom_pan/")
def zoompan_alias():
    from flask import redirect
    return redirect("/zoompan/")

# Ensure /scifi and aliases redirect to /scifi/
@MediaStudioSD2.app.route("/scifi")
@MediaStudioSD2.app.route("/scifi_vision")
@MediaStudioSD2.app.route("/scifi_vision/")
def scifi_alias():
    from flask import redirect
    return redirect("/scifi/")

# Ensure /chat and aliases redirect to /chat/
@MediaStudioSD2.app.route("/chat")
@MediaStudioSD2.app.route("/chat_studio")
@MediaStudioSD2.app.route("/chat_studio/")
def chat_alias():
    from flask import redirect
    return redirect("/chat/")

# Ensure /kobold redirects to Kobold AI on port 5001
@MediaStudioSD2.app.route("/kobold")
@MediaStudioSD2.app.route("/kobold/")
@MediaStudioSD2.app.route("/koboldcpp")
@MediaStudioSD2.app.route("/koboldcpp/")
def kobold_alias():
    from flask import redirect
    return redirect("http://localhost:5001")


class ZoomPanPrefixMiddleware:
    """
    WSGI middleware that rewrites hardcoded absolute links in ZOOM-PAN's
    HTML and JSON responses so that internal paths (/static/, /projects, /api/, etc.)
    remain scoped under the /zoompan sub-path when served by DispatcherMiddleware.
    """
    def __init__(self, wsgi_app, prefix="/zoompan"):
        self.app = wsgi_app
        self.prefix = prefix.rstrip("/")

    def __call__(self, environ, start_response):
        headers_sent = []
        status_code = []

        def custom_start_response(status, headers, exc_info=None):
            status_code.append(status)
            headers_sent.extend(headers)
            return lambda x: None

        app_iter = self.app(environ, custom_start_response)

        content_type = ""
        for name, value in headers_sent:
            if name.lower() == "content-type":
                content_type = value.lower()
                break

        if "text/html" in content_type or "application/json" in content_type:
            try:
                body = b"".join(app_iter)
                if hasattr(app_iter, "close"):
                    app_iter.close()
                text = body.decode("utf-8", errors="replace")

                p = self.prefix
                # Rewrite HTML attributes (don't rewrite if already /zoompan, or external http, or /effects, /remember, or ?root query)
                text = re.sub(r'href="/(?!' + re.escape(p[1:]) + r'/|effects|remember|\?|https?://|//)', f'href="{p}/', text)
                text = re.sub(r'src="/(?!' + re.escape(p[1:]) + r'/|effects|remember|https?://|//)', f'src="{p}/', text)
                text = re.sub(r'action="/(?!' + re.escape(p[1:]) + r'/|effects|remember|https?://|//)', f'action="{p}/', text)

                # Rewrite JS fetch and url calls
                text = re.sub(r"fetch\('(?!\/?" + re.escape(p[1:]) + r'\/)(?!https?:)', f"fetch('{p}/", text)
                text = re.sub(r'fetch\("(?!\/?' + re.escape(p[1:]) + r'\/)(?!https?:)', f'fetch("{p}/', text)
                text = re.sub(r"url:\s*'(?!\/?" + re.escape(p[1:]) + r'\/)(?!https?:)', f"url: '{p}/", text)
                text = re.sub(r'url:\s*"(?!\/?' + re.escape(p[1:]) + r'\/)(?!https?:)', f'url: "{p}/', text)
                text = re.sub(r"load\('(?!\/?" + re.escape(p[1:]) + r'\/)(?!https?:)', f"load('{p}/", text)
                text = re.sub(r'load\("(?!\/?' + re.escape(p[1:]) + r'\/)(?!https?:)', f'load("{p}/', text)
                text = re.sub(r"window\.location\.href\s*=\s*'(?!\/?" + re.escape(p[1:]) + r'\/)(?!https?:)', f"window.location.href = '{p}/", text)
                text = re.sub(r'window\.location\.href\s*=\s*"(?!\/?' + re.escape(p[1:]) + r'\/)(?!https?:)', f'window.location.href = "{p}/', text)

                # Route path strings in JS / JSON (e.g. '/api/', '/upload', '/video/', '/audio/', '/static/')
                text = re.sub(r"'/api/", f"'{p}/api/", text)
                text = re.sub(r'"/api/', f'"{p}/api/', text)
                text = re.sub(r"'/upload", f"'{p}/upload", text)
                text = re.sub(r'"/upload', f'"{p}/upload', text)
                text = re.sub(r"'/video/", f"'{p}/video/", text)
                text = re.sub(r'"/video/', f'"{p}/video/', text)
                text = re.sub(r"'/audio/", f"'{p}/audio/", text)
                text = re.sub(r'"/audio/', f'"{p}/audio/', text)
                text = re.sub(r"'/static/", f"'{p}/static/", text)
                text = re.sub(r'"/static/', f'"{p}/static/', text)

                # Normalize any accidental double slashes (e.g. /zoompan//api -> /zoompan/api)
                text = re.sub(r'/zoompan/+', '/zoompan/', text)

                new_body = text.encode("utf-8")
                new_headers = [(k, v) for k, v in headers_sent if k.lower() != "content-length"]
                new_headers.append(("Content-Length", str(len(new_body))))

                start_response(status_code[0], new_headers)
                return [new_body]
            except Exception:
                start_response(status_code[0], headers_sent)
                return [body]

        start_response(status_code[0], headers_sent)
        return app_iter


zoompan_wsgi = ZoomPanPrefixMiddleware(zoompan_app, prefix="/zoompan")


class SciFiPrefixMiddleware:
    """
    WSGI middleware that rewrites hardcoded absolute links in SciFi Vision Studio's
    HTML and JSON responses so that internal paths (/api/, /assets/, /bgm/, /video/, /resources/, /static/)
    remain scoped under the /scifi sub-path when served by DispatcherMiddleware.
    """
    def __init__(self, wsgi_app, prefix="/scifi"):
        self.app = wsgi_app
        self.prefix = prefix.rstrip("/")

    def __call__(self, environ, start_response):
        headers_sent = []
        status_code = []

        def custom_start_response(status, headers, exc_info=None):
            status_code.append(status)
            headers_sent.extend(headers)
            return lambda x: None

        app_iter = self.app(environ, custom_start_response)

        content_type = ""
        for name, value in headers_sent:
            if name.lower() == "content-type":
                content_type = value.lower()
                break

        if "text/html" in content_type or "application/json" in content_type:
            try:
                body = b"".join(app_iter)
                if hasattr(app_iter, "close"):
                    app_iter.close()
                text = body.decode("utf-8", errors="replace")

                p = self.prefix
                # Rewrite HTML attributes (don't rewrite if already /scifi, or external http, or /effects, /remember, /zoompan, or ?root query)
                text = re.sub(r'href="/(?!' + re.escape(p[1:]) + r'/|effects|remember|zoompan|\?|https?://|//)', f'href="{p}/', text)
                text = re.sub(r'src="/(?!' + re.escape(p[1:]) + r'/|effects|remember|zoompan|https?://|//)', f'src="{p}/', text)
                text = re.sub(r'action="/(?!' + re.escape(p[1:]) + r'/|effects|remember|zoompan|https?://|//)', f'action="{p}/', text)

                # Rewrite JS fetch and url calls
                text = re.sub(r"fetch\('(?!\/?" + re.escape(p[1:]) + r'\/)(?!https?:)', f"fetch('{p}/", text)
                text = re.sub(r'fetch\("(?!\/?' + re.escape(p[1:]) + r'\/)(?!https?:)', f'fetch("{p}/', text)
                text = re.sub(r"fetch\(`(?!\/?" + re.escape(p[1:]) + r'\/)(?!https?:)', f"fetch(`{p}/", text)

                # Route path strings in JS / JSON (e.g. '/api/', '/assets/', '/bgm/', '/video/', '/resources/', '/uploads/', '/exports/', '/static/')
                text = re.sub(r"'/api/", f"'{p}/api/", text)
                text = re.sub(r'"/api/', f'"{p}/api/', text)
                text = re.sub(r"`/api/", f"`{p}/api/", text)
                text = re.sub(r"'/assets/", f"'{p}/assets/", text)
                text = re.sub(r'"/assets/', f'"{p}/assets/', text)
                text = re.sub(r"`/assets/", f"`{p}/assets/", text)
                text = re.sub(r"'/bgm/", f"'{p}/bgm/", text)
                text = re.sub(r'"/bgm/', f'"{p}/bgm/', text)
                text = re.sub(r"'/video/", f"'{p}/video/", text)
                text = re.sub(r'"/video/', f'"{p}/video/', text)
                text = re.sub(r"'/resources/", f"'{p}/resources/", text)
                text = re.sub(r'"/resources/', f'"{p}/resources/', text)
                text = re.sub(r"'/upload", f"'{p}/upload", text)
                text = re.sub(r'"/upload', f'"{p}/upload', text)
                text = re.sub(r"'/exports/", f"'{p}/exports/", text)
                text = re.sub(r'"/exports/', f'"{p}/exports/', text)
                text = re.sub(r"'/static/", f"'{p}/static/", text)
                text = re.sub(r'"/static/', f'"{p}/static/', text)

                # Normalize any accidental double slashes
                text = re.sub(rf'{re.escape(p)}/+', f'{p}/', text)

                new_body = text.encode("utf-8")
                new_headers = [(k, v) for k, v in headers_sent if k.lower() != "content-length"]
                new_headers.append(("Content-Length", str(len(new_body))))

                start_response(status_code[0], new_headers)
                return [new_body]
            except Exception:
                start_response(status_code[0], headers_sent)
                return [body]

        start_response(status_code[0], headers_sent)
        return app_iter


scifi_wsgi = SciFiPrefixMiddleware(scifi_app, prefix="/scifi")

# Mount all applications under unified dispatcher
application = DispatcherMiddleware(MediaStudioSD2.app, {
    "/remember": remember.app,
    "/effects": effects_app,
    "/zoompan": zoompan_wsgi,
    "/scifi": scifi_wsgi,
    "/chat": chat_app,
})

def exit_gracefully(signum, frame):
    print("\n[*] Shutting down unified server...")
    os._exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)

    port = 5200
    print("=" * 65)
    print(f"🚀 Unified Media Studio Suite Starting")
    print(f"   • Media Studio:        http://localhost:{port}/")
    print(f"   • ZoomPan & Comics:    http://localhost:{port}/zoompan")
    print(f"   • Effects Studio:      http://localhost:{port}/effects")
    print(f"   • Remember DB:         http://localhost:{port}/remember")
    print(f"   • SciFi Vision Studio: http://localhost:{port}/scifi")
    print(f"   • AI Q&A & LoRA:       http://localhost:{port}/chat")
    print(f"   • Kobold AI Studio:    http://localhost:5001/ (Alias: /kobold)")
    print("=" * 65)

    run_simple("0.0.0.0", port, application, use_reloader=False, threaded=True)
