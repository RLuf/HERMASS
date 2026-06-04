# Fork strategy — RLuf/hermes-agent

This fork exists for one reason: keep the patch from upstream issue
[#28849](https://github.com/NousResearch/hermes-agent/issues/28849) alive
while still pulling in upstream improvements.

## TL;DR

* `main` mirrors `NousResearch/hermes-agent:main` (we do nothing here).
* `oauth-max` carries one commit on top of `main`: the removal of the
  `mcp_` tool-name prefix loop in `agent/anthropic_adapter.py`. That
  prefix triggers HTTP 400 "out of extra usage" on every tool-bearing
  request when authenticated with a Claude Code OAuth token tied to a
  Pro/Max subscription that has not opted into pay-per-use overage.
* The patch is the only thing the fork adds. Everything else should
  remain identical to upstream.

## How updates flow

The daily workflow `.github/workflows/sync-upstream.yml` does:

1. Fetch `NousResearch/hermes-agent:main`.
2. Merge it into `oauth-max` (merge, not rebase — it keeps history sane
   and only conflicts on the touched hunks).
3. Run `tests/test_oauth_max_patch.py` to confirm the patch survived.
4. If merge was clean and tests pass → open a PR titled
   "sync: upstream/main → oauth-max (clean merge)".
5. If merge had conflicts → invoke Claude CLI with the patch description
   and surrounding upstream context, then re-run the smoke test. Open a
   PR labelled `auto-resolved` (if tests pass) or `needs-human-review`
   (if Claude could not fix everything).

The workflow **never** auto-merges anything into `oauth-max`. A human
(Roger) reviews the PR and merges it.

## The patch in one paragraph

`build_anthropic_kwargs()` used to add `mcp_` to every tool name when the
caller had an OAuth token. Anthropic's overage gate interprets that
prefix as "this is a user-installed MCP-server tool, charge it against
the overage bucket". Max subscribers with overage disabled (the default)
have a zero-sized overage bucket, so every tool-bearing request was
rejected pre-flight. Bare tool names are the only path that hits the
included subscription quota. The official Claude Code CLI sends its own
built-in tools without `mcp_`; only tools coming from
`claude mcp add ...` get the prefix. So we now match that behaviour for
hermes' built-in tools too.

## Updating production (papaimach)

On the box that runs hermes-agent in production:

```bash
cd /usr/local/lib/hermes-agent
git remote set-url origin https://github.com/RLuf/hermes-agent.git
git fetch origin oauth-max
git checkout oauth-max
git reset --hard origin/oauth-max
```

After this, `git pull` is the normal update flow. Always run the smoke
test before letting the gateway resume:

```bash
.venv/bin/python -m pytest tests/test_oauth_max_patch.py -v
```

## Required GitHub Actions secrets

| Secret name              | What for                                                            |
| ------------------------ | ------------------------------------------------------------------- |
| `CLAUDE_CODE_OAUTH_TOKEN`| OAuth token used by Claude CLI to resolve merge conflicts.          |
| `GITHUB_TOKEN`           | Provided automatically by Actions; used for push + PR creation.     |

That's it. No infra to maintain beyond the workflow file.
