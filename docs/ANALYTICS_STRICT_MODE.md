# Strict confirmed-human analytics

The analytics pipeline intentionally optimizes for purity rather than coverage.
JavaScript-disabled visitors, privacy-signal users, old browsers without Fetch
Metadata, and some blockers are not counted.

## Request flow

1. A successful GET of a real public HTML page enters the coarse filter.
2. The filter requires a plausible browser UA and complete top-level navigation
   metadata:
   - `Sec-Fetch-Mode: navigate`
   - `Sec-Fetch-Dest: document`
   - `Sec-Fetch-Site: none`, `same-origin`, or `same-site`
   - `Sec-Fetch-User: ?1`
3. DNT/GPC, prefetch/prerender, known automation UAs, and Cloudflare-verified
   bots are rejected before a seed is issued.
4. An eligible response receives a signed, five-minute, `HttpOnly` analytics
   seed bound to path, daily visitor hash, referrer hostname, and random nonce.
   The response is `private, no-store`.
5. The browser waits until either:
   - the page was visible for at least three seconds and a trusted interaction
     occurred; or
   - the page was visible for at least eight seconds.
6. `POST /api/analytics/confirm` validates the seed, current daily IP hash,
   Origin, Fetch Metadata, rate limit, nonce replay state, Turnstile action, and
   Turnstile hostname.
7. Only then is a row stored with `verification_method = 'turnstile'` and
   `confidence = 100`.
8. A signed `HttpOnly` human cookie, bound to the same daily visitor hash, avoids
   repeating Turnstile on every page until the end of the UTC day.

Rejected requests are not stored individually. `analytics_counters` contains
anonymous per-day totals only. The normal admin query selects only Turnstile
rows while strict mode is enabled.

## Required backend environment

Add these values to `backend/.env` on the production VM:

```dotenv
PORTFOLIO_ANALYTICS_STRICT=true
PORTFOLIO_ANALYTICS_HOSTNAME=ahmet-portfolio.ch
PORTFOLIO_TURNSTILE_SITE_KEY=<public site key>
PORTFOLIO_TURNSTILE_SECRET_KEY=<server-only secret key>
```

Never put the secret key in HTML, JavaScript, screenshots, commits, or client
configuration. If either key is missing, strict analytics fails closed: the
portfolio stays online but no visit is counted.

After updating the environment:

```bash
cd ~/portfolio-reworked/backend
sudo docker compose up -d --build
sudo docker compose logs --tail=100 api
```

## Cloudflare dashboard configuration

### 1. Enable Bot Fight Mode

For the `ahmet-portfolio.ch` zone, open **Security** and find the **Bot traffic**
setting (the exact dashboard grouping can change). Enable **Bot Fight Mode** for
the Free plan.

Reference:
<https://developers.cloudflare.com/use-cases/application-security/bots/>

### 2. Forward the verified-bot signal

Create a **Modify Request Header** Transform Rule for all requests:

```text
Name: Portfolio verified bot signal
Expression: true
Header operation: Set dynamic
Header name: X-Portfolio-Verified-Bot
Value: to_string(cf.client.bot)
```

The backend accepts this header only when the direct network peer is inside the
configured Cloudflare CIDRs. A client that sends the header directly to the
origin is not trusted.

References:

- <https://developers.cloudflare.com/rules/transform/request-header-modification/>
- <https://developers.cloudflare.com/rules/transform/request-header-modification/reference/fields-functions/>

### 3. Create a Turnstile widget

Open **Turnstile**, create one widget with:

```text
Name: Portfolio Analytics
Hostname: ahmet-portfolio.ch
Widget mode: Managed
Pre-clearance: Off
```

The client renders explicitly with:

```text
action: portfolio_analytics
appearance: interaction-only
execution: execute
```

Copy the site key and secret key into `backend/.env`. Siteverify is called only
from FastAPI, with a ten-second timeout. A token is accepted only when
`success` is true and both `hostname` and `action` match.

References:

- <https://developers.cloudflare.com/turnstile/get-started/>
- <https://developers.cloudflare.com/turnstile/get-started/server-side-validation/>
- <https://developers.cloudflare.com/turnstile/get-started/client-side-rendering/widget-configurations/>

## Verification

The original bypass must no longer receive a seed:

```bash
curl -i https://ahmet-portfolio.ch/ \
  -H 'Accept: text/html' \
  -H 'User-Agent: Mozilla/5.0 Chrome/138.0.0.0 Safari/537.36'
```

Expected: no `portfolio_analytics_seed` cookie.

Even a client that spoofs all navigation headers can obtain only a short-lived
seed. It cannot create a visit without a valid, single-use Turnstile token for
the configured hostname and action.

In a normal browser:

1. Open a public page and keep it visible for eight seconds.
2. Open `/admin`, authenticate, and select Analytics.
3. Confirm that the visit has a **Turnstile verified** badge.
4. Expand **Aggregated filter diagnostics** and check the confirmation rate and
   rejection counters.

Automated checks:

```bash
cd backend
python -m unittest discover -s tests -v
python -m compileall app
```

## Connected Cloudflare API permissions

Automation needs an API token with read/write access to the selected zone and
account:

- Zone Settings Read/Edit (Bot Fight Mode), or Bot Management Edit where shown
  by the token UI;
- Transform Rules Read/Edit for `ahmet-portfolio.ch`;
- Turnstile Read/Edit for the account;
- Zone Read so the target can be verified safely.

DNS Edit is not required for this change.
