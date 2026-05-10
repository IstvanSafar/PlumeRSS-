import os, json, requests
from datetime import datetime, timezone

API_KEY = os.environ.get("YOUTUBE_API_KEY", "").strip()
if not API_KEY:
    raise SystemExit("ERROR: YOUTUBE_API_KEY secret is not set or empty.")
BASE = "https://www.googleapis.com/youtube/v3"

CATEGORIES = [
    {"id": "HU_news",     "label": "🇭🇺 Magyar hírek",   "query": "hírek",           "lang": "hu", "region": "HU"},
    {"id": "HU_tech",     "label": "🇭🇺 Magyar tech",     "query": "tech magyarázó",  "lang": "hu", "region": "HU"},
    {"id": "HU_misc",     "label": "🇭🇺 Magyar egyéb",    "query": "podcast magyarázó","lang": "hu", "region": "HU"},
    {"id": "EN_news",     "label": "📰 News",              "query": "news channel",    "lang": "en", "region": "US"},
    {"id": "EN_tech",     "label": "💻 Tech",              "query": "technology",      "lang": "en", "region": "US"},
    {"id": "EN_science",  "label": "🔬 Science",           "query": "science education","lang": "en", "region": "US"},
    {"id": "EN_gaming",   "label": "🎮 Gaming",            "query": "gaming",          "lang": "en", "region": "US"},
    {"id": "EN_finance",  "label": "💼 Finance",           "query": "finance investing","lang": "en", "region": "US"},
]

def yt_get(endpoint, params):
    r = requests.get(f"{BASE}/{endpoint}", params={**params, "key": API_KEY})
    if not r.ok:
        raise requests.HTTPError(f"YouTube API error {r.status_code} on {endpoint}", response=r)
    return r.json()

def fetch_channels(query, lang, region, max_results=12):
    data = yt_get("search", {
        "part": "snippet",
        "type": "channel",
        "q": query,
        "relevanceLanguage": lang,
        "regionCode": region,
        "maxResults": max_results,
        "order": "relevance",
    })
    items = data.get("items", [])
    if not items:
        return []

    channel_ids = [i["snippet"]["channelId"] for i in items]

    data2 = yt_get("channels", {
        "part": "snippet,statistics",
        "id": ",".join(channel_ids),
    })
    details = {c["id"]: c for c in data2.get("items", [])}

    results = []
    for cid in channel_ids:
        c = details.get(cid)
        if not c:
            continue
        subs = int(c["statistics"].get("subscriberCount", 0))
        results.append({
            "id": cid,
            "title": c["snippet"]["title"],
            "description": c["snippet"].get("description", "")[:120],
            "thumbnail": c["snippet"]["thumbnails"].get("default", {}).get("url", ""),
            "subscribers": subs,
            "feedUrl": f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}",
        })

    results.sort(key=lambda x: x["subscribers"], reverse=True)
    return results


output = {"updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "categories": []}

for cat in CATEGORIES:
    print(f"Fetching: {cat['label']} ...")
    channels = fetch_channels(cat["query"], cat["lang"], cat["region"])
    output["categories"].append({
        "id": cat["id"],
        "label": cat["label"],
        "channels": channels,
    })

out_path = os.path.join(os.path.dirname(__file__), "..", "youtube_popular.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Done. {sum(len(c['channels']) for c in output['categories'])} channels written.")
