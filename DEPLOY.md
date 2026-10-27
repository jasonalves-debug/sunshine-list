# Sunshine List 2025 — Vercel Deploy

## Project structure

```
SunshineList/
  vercel.json          ← Vercel config
  sunshine_map.html    ← Map app
  sunshine_map.json    ← Employer map data
  search_index.json    ← Full employee search index (44MB)
  api/
    search.py          ← Serverless search endpoint
    requirements.txt
```

## One-time setup

1. Install Vercel CLI:
   ```
   npm install -g vercel
   ```

2. Log in:
   ```
   vercel login
   ```

## Deploy

From your SunshineList folder:
```
vercel --prod
```

First deploy will ask a few questions:
- Set up and deploy? → Y
- Which scope? → your account
- Link to existing project? → N
- Project name? → sunshine-list (or anything)
- Directory? → ./ (just hit Enter)

After deploy you get a URL like: https://sunshine-list-xxx.vercel.app

## Notes

- `search_index.json` at 44MB is within Vercel's 50MB function bundle limit
- Free tier includes 100GB bandwidth/month — more than enough
- The /search endpoint is a serverless function, spins up on demand
- Cold start on first search may take ~1-2 seconds, subsequent searches are fast
- Next year: just rebuild sunshine_map.json + search_index.json and redeploy with `vercel --prod`

## Local development (no Python server needed for map, only for search)

For local testing with full search:
```
pip install flask
python search_server.py
```

Or just use Vercel dev:
```
vercel dev
```
