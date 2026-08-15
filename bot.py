import os
import json
import cloudscraper
import feedparser
from datetime import datetime

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
CACHE_FILE = "seen_entries.json"

# Advanced stealth scraper to bypass 403 Firewalls
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})

# Instant Direct Feeds (Fixed YouTube ID)
FEEDS = {
    "Sportskeeda Esports": "https://www.sportskeeda.com/esports/feed",
    "BGMI Official YouTube": "https://www.youtube.com/feeds/videos.xml?channel_id=UCe31NPEeRGO0hcznx6Tdb-g",
    "Google News Fallback": "https://news.google.com/rss/search?q=BGMI+redeem+code+when:1d&hl=en-IN&gl=IN&ceid=IN:en"
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
        return

    payload = {
        "embeds": [
            {
                "title": "🚨 New BGMI Code Drop Detected!",
                "description": f"**Headline:** {title}\n\n**Source:** {source_name}\n**Link:** [Click Here to View]({link})\n\n**Redemption Site:** [Official BGMI Redeem Center](https://www.battlegroundsmobileindia.com/redeem)",
                "color": 3447003,
                "footer": {"text": "Ultimate BGMI Cloud Tracker • 24/7 Automated Monitor"},
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
    }
    try:
        scraper.post(WEBHOOK_URL, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
    except Exception as e:
        pass

def check_feeds():
    seen_ids = load_cache()
    new_seen = list(seen_ids)
    
    for name, url in FEEDS.items():
        try:
            response = scraper.get(url, timeout=12)
            if response.status_code != 200:
                continue # Fail silently, try again next loop

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
                        send_discord_alert(title, link, name)
                        new_seen.append(entry_id)

        except Exception:
            pass

    save_cache(new_seen)

if __name__ == "__main__":
    check_feeds()
