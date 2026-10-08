# komodo-tg-relay

Relays [Komodo](https://komo.do) alerts to Telegram. Komodo's Custom Alerter
POSTs its alert JSON to this service, which formats the alert and calls the
Bot API `sendMessage`, optionally into a forum topic.

Single-file Python, standard library only, no auth: run it where only Komodo
Core can reach it (same compose network, no published port).

## Configuration

| Variable | Required | Meaning |
|---|---|---|
| `TG_BOT_TOKEN` | yes | Bot token; the bot must be a member of the chat |
| `TG_CHAT_ID` | yes | Chat id (supergroups start with `-100`) |
| `TG_THREAD_ID` | no | Forum topic id (`message_thread_id`); empty for a plain group |
| `KOMODO_HOST` | no | Core URL, appended as a link to the alerted resource |

Listens on `0.0.0.0:8080`. `POST /alert` accepts an alert, `GET /` answers `ok`.

## Deploy

```yaml
services:
  tg-relay:
    image: ghcr.io/saveweb/komodo-tg-relay:v0.1.0
    restart: unless-stopped
    environment:
      TG_BOT_TOKEN: ${TG_BOT_TOKEN}
      TG_CHAT_ID: ${TG_CHAT_ID}
      TG_THREAD_ID: ${TG_THREAD_ID:-}
      KOMODO_HOST: ${KOMODO_HOST}
    read_only: true
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
```

In Komodo: Settings → Alerters → New, type `Custom`, URL
`http://tg-relay:8080/alert`. The Test button sends a `Test` alert.

## Message format

```
🔴 ServerUnreachable CRITICAL
rice
err: connection refused
http://komodo.internal.example:9120/servers/<id>
```

Resolved alerts get ✅, warnings ⚠️. Every scalar field of the alert's `data`
is listed as `key: value`; `id` is skipped.

## Development

```sh
echo '{"level":"WARNING","resolved":false,"target":{"type":"Server","id":"x"},"data":{"type":"ServerDisk","data":{"name":"cube","path":"/","used_gb":900.2,"total_gb":954}}}' \
  | TG_BOT_TOKEN=t TG_CHAT_ID=c python3 -c 'import sys,json,app; print(app.fmt(json.load(sys.stdin)))'
```

Images are built by GitHub Actions on every push to `main` (`:main`, `:sha-<short>`)
and on `v*` tags (`:vX.Y.Z`, `:latest`).
