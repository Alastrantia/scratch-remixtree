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
