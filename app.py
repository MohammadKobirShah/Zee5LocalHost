import os
import requests
from flask import Flask, Response, request

app = Flask(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 ygx/69.1 Safari/537.36"
COOKIES_FILE = "cookies.txt"

def load_cookies():
    return open(COOKIES_FILE).read().strip() if os.path.exists(COOKIES_FILE) else ""


@app.route("/")
def home():
    return """
    <h2>🎬 Zee Proxy with Audio Support</h2>
    <p>Usage: <code>/play/&lt;groupid&gt;/&lt;channelid&gt;.m3u8</code></p>
    <p>Example: <code>/play/2105554/ZeeBanglaHDELE.m3u8</code></p>
    """


@app.route("/play/<groupid>/<channelid>.m3u8")
def play(groupid, channelid):
    """
    Proxy master playlist for group+channel, rewrite ALL URIs (video+audio) to /proxy/
    """
    base_url = f"https://z5ak-cmaflive.zee5.com/cmaf/live/{groupid}/{channelid}/index-connected.m3u8"
    headers = {"User-Agent": USER_AGENT, "Cookie": load_cookies()}
    r = requests.get(base_url, headers=headers, timeout=10)

    if r.status_code != 200:
        return f"❌ Failed to fetch master manifest: {r.status_code}", 500

    playlist = r.text.splitlines()
    rewritten = []

    for line in playlist:
        if line.startswith("#") or line.strip() == "":
            rewritten.append(line)
        else:
            # Force all references through /proxy/
            proxied = f"/proxy/cmaf/live/{groupid}/{channelid}/{line}"
            rewritten.append(proxied)

    return Response("\n".join(rewritten), content_type="application/vnd.apple.mpegurl")


@app.route("/proxy/<path:subpath>")
def proxy(subpath):
    """
    Proxies EVERYTHING:
      - sub-playlists (master_1080p.m3u8, master_aud.m3u8)
      - media segments (.ts/.m4s)
    """
    url = f"https://z5ak-cmaflive.zee5.com/{subpath}"
    headers = {"User-Agent": USER_AGENT, "Cookie": load_cookies()}

    if request.headers.get("Range"):
        headers["Range"] = request.headers["Range"]

    r = requests.get(url, headers=headers, stream=True, timeout=15)

    # If it’s a .m3u8, rewrite its references again (video or audio)
    if subpath.endswith(".m3u8"):
        playlist = r.text.splitlines()
        rewritten = []

        prefix = "/".join(subpath.split("/")[:-1])

        for line in playlist:
            if line.startswith("#") or line.strip() == "":
                rewritten.append(line)
            else:
                proxied = f"/proxy/{prefix}/{line}"
                rewritten.append(proxied)

        return Response("\n".join(rewritten), content_type="application/vnd.apple.mpegurl")

    # Otherwise proxy binary segments (.ts/.m4s audio or video)
    def generate():
        for chunk in r.iter_content(64 * 1024):
            yield chunk

    return Response(
        generate(),
        status=r.status_code,
        headers={k: v for k, v in r.headers.items()
                 if k.lower() in ["content-type","content-length","accept-ranges","content-range"]},
        content_type=r.headers.get("Content-Type", "video/mp2t"),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
