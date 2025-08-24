import os
import requests
from flask import Flask, Response, request

app = Flask(__name__)

# Base stream URL
BASE_URL = "https://z5ak-cmaflive.zee5.com/cmaf/live/2105554/{channelid}/index-connected.m3u8"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 ygx/69.1 Safari/537.36"
COOKIES_FILE = "cookies.txt"


def load_cookies():
    """Always reload cookies.txt dynamically."""
    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "r") as f:
            return f.read().strip()
    return ""


@app.route("/")
def home():
    return """
    <h2>🎬 Transparent Zee Proxy</h2>
    <p>Example: <code>http://localhost:5000/play/zee_tv.m3u8</code></p>
    """


@app.route("/play/<channelid>.m3u8")
def play(channelid):
    """
    Proxy the original Zee master playlist (.m3u8)
    """
    url = BASE_URL.format(channelid=channelid)

    headers = {
        "User-Agent": USER_AGENT,
        "Cookie": load_cookies(),
    }
    if request.headers.get("Range"):
        headers["Range"] = request.headers["Range"]

    try:
        r = requests.get(url, headers=headers, stream=True, timeout=15)
        r.raise_for_status()
    except Exception as e:
        return f"❌ Error fetching playlist: {e}", 500

    def generate():
        for chunk in r.iter_content(chunk_size=1024 * 32):
            if chunk:
                yield chunk

    return Response(
        generate(),
        status=r.status_code,
        headers={k: v for k, v in r.headers.items()},
        content_type=r.headers.get("Content-Type", "application/vnd.apple.mpegurl"),
    )


@app.route("/proxy/<path:subpath>")
def proxy(subpath):
    """
    Transparent proxy for ALL other requests (sub-playlists, segments, audio files).
    No rewriting — just forward and deliver.
    """
    url = f"https://z5ak-cmaflive.zee5.com/{subpath}"

    headers = {
        "User-Agent": USER_AGENT,
        "Cookie": load_cookies(),
    }
    if request.headers.get("Range"):
        headers["Range"] = request.headers["Range"]

    try:
        r = requests.get(url, headers=headers, stream=True, timeout=15)
        r.raise_for_status()
    except Exception as e:
        return f"❌ Error fetching: {e}", 500

    def generate():
        for chunk in r.iter_content(chunk_size=1024 * 64):
            if chunk:
                yield chunk

    return Response(
        generate(),
        status=r.status_code,
        headers={k: v for k, v in r.headers.items()},
        content_type=r.headers.get("Content-Type", "application/octet-stream"),
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
