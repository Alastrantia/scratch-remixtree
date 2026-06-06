# deploys

both halves of the site auto-deploy from `main` via github actions now. the workflows
live in `.github/workflows/`. they're **gated on secrets**, so until you add them the
deploy steps just skip (the runs stay green, no scary red X).

## frontend → cloudflare pages

`deploy-frontend.yml` runs `wrangler pages deploy web/frontend` whenever something in
`web/frontend/**` changes (or you hit "Run workflow" manually).

add these in **repo → Settings → Secrets and variables → Actions**:

| name | kind | where to get it |
| --- | --- | --- |
| `CLOUDFLARE_API_TOKEN` | secret | Cloudflare dashboard → My Profile → API Tokens → Create Token, give it **Account · Cloudflare Pages · Edit** |
| `CLOUDFLARE_ACCOUNT_ID` | secret | Cloudflare dashboard → right sidebar on any domain, or Workers & Pages overview |
| `CF_PAGES_PROJECT` | variable (optional) | only if your Pages project isn't named `scratch-remixtree` |

## backend → render

`deploy-backend.yml` POSTs your Render deploy hook. it fires on:
- changes to `web/backend/**`
- **every successful `Publish Python Package` run** — so when you tag a new version,
  render redeploys and finally pulls the fresh `remixtree` off pypi (this was the whole
  "backend is running an old version" headache, sorted)
- manually via "Run workflow"

add this secret:

| name | kind | where to get it |
| --- | --- | --- |
| `RENDER_DEPLOY_HOOK_URL` | secret | Render → your service → Settings → **Deploy Hook**, copy the URL |

## heads up

- if you already have render's / cloudflare's **native git auto-deploy** turned on for
  pushes, you'll get deployed twice on a push. either flip those off, or delete the
  `push:` trigger from the matching workflow. the publish-triggered render redeploy is the
  bit native auto-deploy *can't* do, so that one's worth keeping either way.
- the `sapi-proxy` worker isn't wired up here, it barely ever changes — push it with
  `wrangler deploy` from `web/sapi-proxy/` when you do touch it.

## keeping the backend awake (important!)

render's free tier sleeps after ~15min idle and cold-starts for ~50s. two things fight that:

1. **cloudflare cron (the reliable one)** — `web/sapi-proxy` now pings `/health` every 5 min
   via a cron trigger. it auto-deploys via `deploy-worker.yml` whenever `web/sapi-proxy/**`
   changes — **but** that needs `CLOUDFLARE_API_TOKEN` to have **Workers Scripts: Edit** perms
   (the pages token only had Pages:Edit, so widen it or make a combined token).
   prefer doing it by hand? `cd web/sapi-proxy && npx wrangler deploy`.
   either way, check the cron stuck with `npx wrangler triggers` (or Cloudflare dashboard →
   the worker → Settings → Triggers → Cron Triggers, should show `*/5 * * * *`).
2. **github actions backup** — `keep_warm.yml` still pings every 5 min in case cloudflare
   ever hiccups. belt and suspenders.

the frontend also pre-warms `/health` on page load and rides out a cold start with a
"waking up…" message + retries, so even if both pingers miss, worst case is a ~50s wait
with a friendly message instead of an error.
