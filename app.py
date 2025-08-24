import os
import requests
from flask import Flask, Response, request

app = Flask(__name__)

BASE_URL = "https://z5ak-cmaflive.zee5.com/cmaf/live/2105554/{channelid}/index-connected.m3u8"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 ygx/69.1 Safari/537.36"
COOKIES_FILE = "cookies.txt"


def load_cookies():
    return open(COOKIES_FILE).read().strip() if os.path.exists(COOKIES_FILE) else ""


@app.route("/")
def home():
    return "<h2>🎬 Zee Proxy</h2><p>Example: /play/zee_tv.m3u8</p>"


@app.route("/play/<channelid>.m3u8")
def play(channelid):
    """
    Fetch original master playlist and return intact (no rewrite).
    """
    url = BASE_URL.format(channelid=channelid)
    headers = {"User-Agent": USER_AGENT, "Cookie": load_cookies()}
    r = requests.get(url, headers=headers, timeout=10)

    if r.status_code != 200:
        return f"❌ Failed to fetch manifest {channelid}: {r.status_code}", 500

    # 🔑 Return playlist manifest text to VLC
    return Response(r.text, content_type="application/vnd.apple.mpegurl")


@app.route("/proxy/<path:subpath>")
def proxy(subpath):
    """
    Pass-through proxy for media chunks and nested playlists.
    """
    url = f"https://z5ak-cmaflive.zee5.com/{subpath}"
    headers = {"User-Agent": USER_AGENT, "Cookie": load_cookies()}

    # Pass Range header (required for ts/m4s chunks)
    if request.headers.get("Range"):
        headers["Range"] = request.headers["Range"]

    r = requests.get(url, headers=headers, stream=True, timeout=15)

    def generate():
        for chunk in r.iter_content(64 * 1024):
            yield chunk

    return Response(
        generate(),
        status=r.status_code,
        headers={k: v for k, v in r.headers.items()},
        content_type=r.headers.get("Content-Type", "application/octet-stream"),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)  # run Flask on 8080
