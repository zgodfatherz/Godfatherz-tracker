import os
import json
import requests
import feedparser
from datetime import datetime

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
CACHE_FILE = "seen_entries.json"

# Stealth headers to avoid website blocks
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# Targeted multi-source feeds
FEEDS = {
    "Google News (Aggregated Gaming Portals)": "https://news.google.com/rss/search?q=BGMI+redeem+code+when:1d&hl=en-IN&gl=IN&ceid=IN:en",
    "Sportskeeda Esports": "https://www.sportskeeda.com/esports/feed",
    "BGMI Official YouTube": "https://www.youtube.com/feeds/videos.xml?channel_id=UCn0X3i_qC2v0A-hW9v2sM8w"
}

TRIGGER_KEYWORDS = [
    "redeem", "code", "reward", "redemption", "free uc", 
    "diver set", "outfit", "glacier", "coupon", "battlegrounds"
]

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache[-200:], f, indent=2)

def send_discord_alert(title, link, source_name):
    if not WEBHOOK_URL:
        print("Error: DISCORD_WEBHOOK_URL not configured.")
        return

    payload = {
        "embeds": [
            {
                "title": "🚨 New BGMI Code Drop Detected!",
                "description": f"**Headline:** {title}\n\n**Source:** {source_name}\n**Article/Post Link:** [Click Here to View]({link})\n\n**Redemption Site:** [Official BGMI Redeem Center](https://www.battlegroundsmobileindia.com/redeem)",
                "color": 3447003,
                "footer": {"text": "Ultimate BGMI Cloud Tracker • 24/7 Automated Monitor"},
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
    }
    try:
        requests.post(WEBHOOK_URL, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
    except Exception as e:
        print(f"Failed to post to Discord: {e}")

def send_block_warning(source_name, error_msg):
    if not WEBHOOK_URL:
        return
    payload = {
        "embeds": [
            {
                "title": "⚠️ Tracker Block / Warning",
                "description": f"Failed to fetch data from **{source_name}**.\n**Reason:** `{error_msg}`\n*Other feeds remain active.*",
                "color": 15158332,
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
    }
    try:
        requests.post(WEBHOOK_URL, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
    except Exception as e:
        print(f"Failed to post block warning: {e}")

def check_feeds():
    seen_ids = load_cache()
    new_seen = list(seen_ids)
    
    for name, url in FEEDS.items():
        try:
            response = requests.get(url, headers=HEADERS, timeout=12)
            if response.status_code == 403:
                send_block_warning(name, "HTTP 403 Forbidden (Blocked)")
                continue
            elif response.status_code == 429:
                send_block_warning(name, "HTTP 429 Rate Limited")
                continue
            elif response.status_code != 200:
                send_block_warning(name, f"HTTP Status {response.status_code}")
                continue

            feed = feedparser.parse(response.content)
            for entry in feed.entries:
                entry_id = getattr(entry, "id", getattr(entry, "link", None))
                if not entry_id or entry_id in seen_ids:
                    continue

                title = getattr(entry, "title", "")
                summary = getattr(entry, "summary", "")
                combined_text = f"{title} {summary}".lower()

                if "bgmi" in combined_text or "battlegrounds mobile india" in combined_text:
                    if any(kw in combined_text for kw in TRIGGER_KEYWORDS):
                        link = getattr(entry, "link", "https://www.battlegroundsmobileindia.com")
                        print(f"Match found: {title}")
                        send_discord_alert(title, link, name)
                        new_seen.append(entry_id)

        except requests.exceptions.RequestException as req_err:
            send_block_warning(name, str(req_err))
        except Exception as e:
            print(f"Error checking {name}: {e}")

    save_cache(new_seen)

if __name__ == "__main__":
    check_feeds()
  
