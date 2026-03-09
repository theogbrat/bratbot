# BratBot 👑

Kick channel rewards bot for @theogbrat_ — automatically posts in chat when a viewer redeems a channel point reward and directs them to Discord.

## Setup

### Environment Variables (set in Railway)

| Variable | Description |
|---|---|
| `KICK_CLIENT_ID` | Your Kick app Client ID |
| `KICK_CLIENT_SECRET` | Your Kick app Client Secret |
| `KICK_ACCESS_TOKEN` | Your OAuth user access token |
| `KICK_CHANNEL_ID` | Your numeric Kick channel ID |
| `KICK_WEBHOOK_SECRET` | Webhook secret from Kick dev settings |
| `DISCORD_LINK` | Your Discord invite link |
| `RAILWAY_PUBLIC_DOMAIN` | Auto-set by Railway |

## How it works

1. Viewer redeems a channel point reward on Kick
2. Kick sends a webhook to BratBot
3. BratBot posts a message in chat tagging the viewer with the Discord link
4. Viewer opens a ticket in Discord to claim their reward

## Endpoints

- `GET /` — health check
- `POST /webhook` — Kick webhook receiver
