import os
import requests
from flask import Flask, Response

app = Flask(__name__)

BASE_URL = "https://z5ak-cmaflive.zee5.com/cmaf/live/2105554/{channelid}/index-connected.m3u8"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 ygx/69.1 Safari/537.36"

COOKIES_FILE = "cookies.txt"


def load_cookies():
    """Load cookies from cookies.txt dynamically each request"""
    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "r") as f:
            return f.read().strip()
    return ""


@app.route("/")
def home():
    return """
    <h2>🎬 Local Zee Proxy</h2>
    <p>Example: http://localhost:5000/play/zee_tv.m3u8</p>
    """


@app.route("/play/<channelid>.m3u8")
def play(channelid):
    url = BASE_URL.format(channelid=channelid)
    headers = {
        "User-Agent": USER_AGENT,
        "Cookie": load_cookies(),
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
    except Exception as e:
        return f"❌ Error fetching playlist: {e}", 500

    playlist = r.text
    rewritten = []

    # Rewrite all stream segment URLs to our proxy
    for line in playlist.splitlines():
        if line.strip().startswith("#") or line.strip() == "":
            rewritten.append(line)
        else:
            if line.startswith("http"):
                proxied = line.replace("https://z5ak-cmaflive.zee5.com/", "/proxy/")
            else:
                proxied = "/proxy/" + line.lstrip("/")
            rewritten.append(proxied)

    return Response("\n".join(rewritten), content_type="application/vnd.apple.mpegurl")


@app.route("/proxy/<path:subpath>")
def proxy(subpath):
    url = f"https://z5ak-cmaflive.zee5.com/{subpath}"
    headers = {
        "User-Agent": USER_AGENT,
        "Cookie": load_cookies(),
    }

    try:
        r = requests.get(url, headers=headers, stream=True, timeout=10)
        r.raise_for_status()
    except Exception as e:
        return f"❌ Error fetching segment: {e}", 500

    def generate():
        for chunk in r.iter_content(chunk_size=1024 * 32):
            if chunk:
                yield chunk

    mime = r.headers.get("Content-Type", "video/mp2t")
    return Response(generate(), content_type=mime)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
