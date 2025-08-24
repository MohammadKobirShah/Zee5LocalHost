Perfect 🙌 You’re a beginner, so let’s go super clear with a **step‑by‑step A‑to‑Z guide**.  

We’re setting up:  
- The **Flask proxy app** (Python) on your VPS (localhost)  
- Automatic **cookies updater** (via GitHub Actions + cron pull)  
- Optional: **Cloudflare Tunnel** to expose with a custom domain  

No assumptions, I’ll explain each step like we’re building LEGO 🚧.  

---

# 🅰️ A-Z Guide

---

## 1️⃣ Prepare Your VPS

1. Update system:
```bash
sudo apt update && sudo apt upgrade -y
```

2. Install Python & Git:
```bash
sudo apt install python3 python3-pip git -y
```

---

## 2️⃣ Clone the Project

1. Open terminal, go to your VPS home:
```bash
cd ~
```

2. Clone your repo (example: `zee5-proxy-railway`):
```bash
git clone https://github.com/MohammadKobirShah/Zee5LocalHost.git
cd Zee5LocalHost
```

> Replace `YOURUSER` with your GitHub username.

---

## 3️⃣ Install Required Python Packages

```bash
pip3 install -r requirements.txt
```

This will install:
- `flask`
- `requests`

---

## 4️⃣ Run Flask App (Localhost Proxy)

```bash
python3 app.py
```

- By default it runs on:  
  `http://127.0.0.1:8080`  

- Test by opening in **VLC** on your VPS desktop (if GUI installed):  
  `http://127.0.0.1:8080/play/zee_tv.m3u8`

---

## 5️⃣ Automatic Cookies Refresh (GitHub Actions + Cron)

You already have GitHub Action workflow (`fetch-cookies.yml`) set up.  
It updates `cookies.txt` **inside GitHub every hour**.  

Now, VPS must **pull those changes** periodically:

1. Edit Cron:
```bash
crontab -e
```

2. Add this line (every hour):
```bash
0 * * * * cd /root/Zee5LocalHost && git pull -q
```

Save & exit (CTRL+O then ENTER, CTRL+X for nano).  

Now, every hour VPS pulls the updated `cookies.txt` → Flask automatically reads fresh cookies **per request**.  

---

## 6️⃣ Run Flask in Background (Optional but Recommended)

Instead of keeping `python3 app.py` open, use **systemd service** so it runs even after logout:

1. Create service file:
```bash
sudo nano /etc/systemd/system/Zee5LocalHost.service
```

2. Paste this:

```ini
[Unit]
Description=Zee5 Proxy Flask App
After=network.target

[Service]
WorkingDirectory=/root/Zee5LocalHost
ExecStart=/usr/bin/python3 /root/Zee5LocalHost/app.py
Restart=always
User=root

[Install]
WantedBy=multi-user.target
```

3. Save (CTRL+O, ENTER, CTRL+X)

4. Enable and start:
```bash
sudo systemctl enable Zee5LocalHost
sudo systemctl start Zee5LocalHost
```

5. Check if working:
```bash
sudo systemctl status Zee5LocalHost
```

✅ Your proxy is always running now.

---

## 7️⃣ Expose to Internet (Cloudflare Tunnel)

Because your VPS has **no public IPv4** → normal port forwarding won’t work.  
Use **Cloudflare Tunnel**.

1. Install:
```bash
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

2. Login:
```bash
cloudflared tunnel login
```
➡ Opens a browser → pick your Cloudflare account + domain

3. Create tunnel:
```bash
cloudflared tunnel create zee5-tunnel
```

4. Configure:
```bash
nano ~/.cloudflared/config.yml
```

Paste this:

```yaml
tunnel: <YOUR_TUNNEL_ID>
credentials-file: /root/.cloudflared/<YOUR_TUNNEL_ID>.json

ingress:
  - hostname: zee5.yourdomain.com
    service: http://localhost:5000
  - service: http_status:404
```

(Replace `<YOUR_TUNNEL_ID>` and `zee5.yourdomain.com` with your values).  

5. Add DNS Route:
```bash
cloudflared tunnel route dns zee5-tunnel zee5.yourdomain.com
```

6. Start tunnel test:
```bash
cloudflared tunnel run zee5-tunnel
```

7. Permanent service:
```bash
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

---

## 8️⃣ Test Everything

- In VLC:  
  ```
  https://zee5.yourdomain.com/play/zee_tv.m3u8
  ```

- On localhost VPS:  
  ```
  http://127.0.0.1:5000/play/zee_tv.m3u8
  ```

🎉 It should now play smoothly.

---

# ✅ Recap  

- **Flask App** serves `.m3u8` playlists proxying Zee.  
- **cookies.txt** auto-updated by GitHub Actions.  
- **Cron** pulls latest cookies hourly.  
- **Systemd service** ensures app always runs in background.  
- **Cloudflare Tunnel** exposes your service to the Internet on a custom domain, despite no public IP.  

---

🔥 That’s the full beginner-friendly pipeline from ZERO → fully working **self-updating Zee proxy with domain access**.  

---

Would you like me to now **bundle these instructions + configs into the README.md** of your repo, so your project is instantly beginner-friendly for others too?
