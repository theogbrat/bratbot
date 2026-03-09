import os
import hmac
import hashlib
import httpx
import asyncio
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

app = FastAPI()

# ── Config (set these as Railway env vars) ──────────────────────────────────
CLIENT_ID       = os.environ["KICK_CLIENT_ID"]
CLIENT_SECRET   = os.environ["KICK_CLIENT_SECRET"]
ACCESS_TOKEN    = os.environ["KICK_ACCESS_TOKEN"]   # your OAuth user token
CHANNEL_ID      = os.environ["KICK_CHANNEL_ID"]     # your numeric channel ID
WEBHOOK_SECRET  = os.environ.get("KICK_WEBHOOK_SECRET", "")
DISCORD_LINK    = os.environ.get("DISCORD_LINK", "https://discord.gg/YOURLINK")

KICK_API        = "https://api.kick.com/public/v1"

# ── Helpers ─────────────────────────────────────────────────────────────────

def verify_signature(secret: str, body: bytes, sig_header: str) -> bool:
    """Verify Kick webhook signature."""
    if not secret or not sig_header:
        return True  # Skip verification if no secret set yet
    expected = "sha256=" + hmac.new(
        secret.encode(), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, sig_header)


async def send_chat_message(message: str):
    """Post a message to your Kick chat."""
    url = f"{KICK_API}/chat"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "broadcaster_id": int(CHANNEL_ID),
        "content": message,
        "type": "bot",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code not in (200, 201):
            print(f"[BratBot] Chat error {resp.status_code}: {resp.text}")
        else:
            print(f"[BratBot] Sent: {message}")


# ── Reward messages ─────────────────────────────────────────────────────────

def build_message(event_type: str, username: str, reward_title: str) -> str:
    """Return the right chat message for a redemption."""
    reward_lower = reward_title.lower()

    if "steam" in reward_lower or "gift" in reward_lower:
        return (
            f"👑 @{username} has redeemed {reward_title}! "
            f"Head to our Discord and open a ticket in 🎫 | get-support to claim your prize 🖤 {DISCORD_LINK}"
        )
    elif "giveaway" in reward_lower or "won" in reward_lower:
        return (
            f"🏆 @{username} is claiming their giveaway prize! "
            f"Open a ticket in 🎫 | get-support on our Discord 🖤 {DISCORD_LINK}"
        )
    else:
        # Generic fallback for any other reward
        return (
            f"👑 @{username} just redeemed {reward_title}! "
            f"Head to our Discord if you need to claim anything 🖤 {DISCORD_LINK}"
        )


# ── Webhook endpoint ─────────────────────────────────────────────────────────

@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.body()

    # Verify signature
    sig = request.headers.get("Kick-Event-Signature", "")
    if not verify_signature(WEBHOOK_SECRET, body, sig):
        raise HTTPException(status_code=401, detail="Invalid signature")

    event_type = request.headers.get("Kick-Event-Type", "")
    data = await request.json()

    print(f"[BratBot] Event: {event_type} | Data: {data}")

    # Channel reward redemption
    if event_type == "channel.reward.redemption.created":
        redeemer  = data.get("redeemer", {})
        username  = redeemer.get("username", "someone")
        reward    = data.get("reward", {})
        title     = reward.get("title", "a reward")
        message   = build_message(event_type, username, title)
        background_tasks.add_task(send_chat_message, message)

    return JSONResponse({"status": "ok"})


# ── Health check ─────────────────────────────────────────────────────────────

@app.get("/")
async def health():
    return {"status": "BratBot is running 🖤"}


# ── Subscribe to events on startup ──────────────────────────────────────────

@app.on_event("startup")
async def subscribe_events():
    """Auto-subscribe to channel reward redemption events on boot."""
    webhook_url = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    if not webhook_url:
        print("[BratBot] No RAILWAY_PUBLIC_DOMAIN set — skipping auto-subscribe")
        return

    webhook_url = f"https://{webhook_url}/webhook"
    url = f"{KICK_API}/events/subscriptions"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "events": [
            {"name": "channel.reward.redemption.created", "version": 1}
        ],
        "method": "webhook",
        "webhook_url": webhook_url,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code in (200, 201):
            print(f"[BratBot] ✅ Subscribed to reward redemptions → {webhook_url}")
        else:
            print(f"[BratBot] ⚠️ Subscription failed {resp.status_code}: {resp.text}")
