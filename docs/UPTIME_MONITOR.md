# Free Uptime Monitor

Monitor this URL:

```text
https://ahmet-portfolio.ch/api/health
```

Recommended interval: every 5 to 15 minutes. This endpoint is cheap and returns a tiny JSON response, so it is safe for the 1 GB Oracle VM.

## Option A: UptimeRobot Free

1. Create a free account at UptimeRobot.
2. Add a new HTTP(s) monitor.
3. URL: `https://ahmet-portfolio.ch/api/health`.
4. Interval: 5 minutes if available on your free plan, otherwise 10 or 15 minutes.
5. Alert contact: your email.

## Option B: Better Stack Free

1. Create a free Better Stack account.
2. Create an uptime monitor.
3. URL: `https://ahmet-portfolio.ch/api/health`.
4. Check frequency: 5 to 15 minutes.
5. Enable email alerts.

## Option C: cron-job.org

1. Create a free cron-job.org account.
2. Add a cron job for `https://ahmet-portfolio.ch/api/health`.
3. Schedule it every 5 to 15 minutes.
4. Enable failure notifications.

## What Alerts Mean

One failed check can mean a temporary Cloudflare, DNS, network, or VM hiccup. Two or more failures in a row usually means you should SSH into the VM and check:

```bash
cd ~/portfolio-reworked/backend
sudo docker compose ps
sudo docker compose logs --tail=100
curl -s http://localhost/api/health
```

## What Not To Do

Do not run CPU burners, fake traffic loops, browser refresh loops, or artificial load to keep the VM awake. Oracle Always-Free VMs do not need that, and it can waste the tiny CPU budget. A normal uptime monitor hitting `/api/health` every 5 to 15 minutes is enough.
