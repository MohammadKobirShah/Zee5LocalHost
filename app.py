import os
import requests
from flask import Flask, Response, request

app = Flask(__name__)

# Base Zee5 playlist URL
BASE_URL = "https://z5ak-cmaflive.zee5.com/cmaf/live/2105554/{channelid}/index-connected.m3u8"

# Custom User-Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 ygx/69.1 Safari/537.36"

# File containing cookies (auto-updated by GitHub Actions + cron git pull)
COOKIES_FILE = "cookies.txt"


def load_cookies():
    """Load cookies dynamically from file."""
    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "r") as f:
            return f.read().strip()
    return ""


@app.route("/")
def home():
    return """
    <h2>🎬 Local Zee Proxy</h2>
    <p>Example: <code>http://localhost:5000/play/zee_tv.m3u8</code></p>
    """


@app.route("/play/<channelid>.m3u8")
def play(channelid):
    """
    Fetch master playlist for a channel, rewrite URLs → proxy.
    """
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
    """
    Proxy handler for:
      - Sub-playlists (.m3u8) → rewrite & return
      - Segments (.ts/.m4s) → stream back transparently
    """
    url = f"https://z5ak-cmaflive.zee5.com/{subpath}"

    # Forward essential headers (esp. Range for streaming)
    headers = {
        "User-Agent": USER_AGENT,
        "Cookie": load_cookies(),
    }
    if request.headers.get("Range"):
        headers["Range"] = request.headers["Range"]

    try:
        r = requests.get(url, headers=headers, stream=True, timeout=10)
        r.raise_for_status()
    except Exception as e:
        return f"❌ Error fetching: {e}", 500

    if subpath.endswith(".m3u8"):
        # Rewrite sub-playlist
        playlist = r.text
        rewritten = []
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

    # Otherwise stream segments directly
    def generate():
        for chunk in r.iter_content(chunk_size=1024 * 32):
            if chunk:
                yield chunk

    content_type = r.headers.get("Content-Type", "video/mp2t")
    status_code = r.status_code
    response_headers = {
        k: v for k, v in r.headers.items()
        if k.lower() in ["content-type", "content-length", "accept-ranges", "content-range"]
    }

    return Response(generate(), status=status_code, headers=response_headers, content_type=content_type)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
