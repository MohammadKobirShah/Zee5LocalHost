import os
import requests
from flask import Flask, Response

app = Flask(__name__)

# Base m3u8 URL from Zee
BASE_URL = "https://z5ak-cmaflive.zee5.com/cmaf/live/2105554/{channelid}/index-connected.m3u8"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 ygx/69.1 Safari/537.36"

# Load cookies
COOKIES_FILE = "cookies.txt"
with open(COOKIES_FILE, "r") as f:
    COOKIE_STRING = f.read().strip()


@app.route("/")
def home():
    return """
    <h2>🎬 Zee Proxy Stream</h2>
    <p>Try a URL like: <code>/play/zee_tv.m3u8</code></p>
    """


@app.route("/play/<channelid>.m3u8")
def play(channelid):
    """
    Fetches the m3u8 playlist, rewrites all segment URLs to proxy through us
    """
    url = BASE_URL.format(channelid=channelid)

    headers = {
        "User-Agent": USER_AGENT,
        "Cookie": COOKIE_STRING,
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
    except Exception as e:
        return f"❌ Error fetching playlist: {e}", 500

    playlist = r.text

    # Rewrite ALL absolute/relative segment URLs to /proxy/
    rewritten = []
    for line in playlist.splitlines():
        if line.strip().startswith("#"):  # comments/metadata
            rewritten.append(line)
        elif line.strip() == "":
            rewritten.append(line)
        else:
            # rewrite url to go through /proxy/
            if line.startswith("http"):
                proxied = line.replace("https://z5ak-cmaflive.zee5.com/", "/proxy/")
            else:
                proxied = "/proxy/" + line.lstrip("/")
            rewritten.append(proxied)

    new_playlist = "\n".join(rewritten)

    return Response(new_playlist, content_type="application/vnd.apple.mpegurl")


@app.route("/proxy/<path:subpath>")
def proxy(subpath):
    """
    Proxies video chunks (ts/m4s) via us
    """
    url = f"https://z5ak-cmaflive.zee5.com/{subpath}"

    headers = {
        "User-Agent": USER_AGENT,
        "Cookie": COOKIE_STRING,
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
