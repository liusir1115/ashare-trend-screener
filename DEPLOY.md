# Public MVP Deployment

This project is ready to be deployed as a public MVP even before Tushare is integrated.

## Current public-MVP behavior

- The frontend is served directly by FastAPI.
- The backend exposes `/api/mvp/bootstrap` and `/api/mvp/strategy`.
- The data layer tries live AKShare samples first.
- If live data is unavailable, it falls back to bundled demo samples.

That means the app still opens and stays usable even when the free upstream data source is unstable.

## Recommended platforms

- Render
- Railway

Both work well for a small Python + FastAPI MVP.

## Recommended environment variables

- `MVP_FORCE_FALLBACK=true`
- `MVP_CACHE_TTL_SECONDS=1800`

Why:

- `MVP_FORCE_FALLBACK=true` makes the public demo stable by avoiding live AKShare calls.
- `MVP_CACHE_TTL_SECONDS` reduces repeated calls when you do allow live AKShare samples.

## Render

1. Push this project to a Git repository.
2. Create a new `Web Service` in Render.
3. Point it to the repository.
4. Render will detect [render.yaml](/C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/render.yaml) and [Dockerfile](/C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/Dockerfile).
5. Add the recommended environment variables.
6. Deploy and open the generated URL.

Health check:

- `GET /health`

## Railway

1. Push this project to a Git repository.
2. Create a new Railway project from GitHub.
3. Railway can use either [Dockerfile](/C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/Dockerfile) or [railway.json](/C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/railway.json).
4. Add the recommended environment variables.
5. Deploy and open the generated domain.

## Production entrypoint

Server entrypoint:

- [server.py](/C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/src/ashare_strategy/server.py)

Environment variables used by the server:

- `HOST`
- `PORT`
- `MVP_FORCE_FALLBACK`
- `MVP_CACHE_TTL_SECONDS`

Default bind:

- `0.0.0.0:8000`

## Suitable for

- Small product testing
- Strategy intake flow validation
- UX validation
- Public demo links

## Not suitable for yet

- Formal trading reference
- Minute-level real-time decisions
- Paid public release

## What improves after Tushare

Once Tushare is integrated, this same public MVP can be upgraded with:

- more stable daily data
- better chip-distribution data
- stronger backtest credibility
- better separation between main board and STAR board results
