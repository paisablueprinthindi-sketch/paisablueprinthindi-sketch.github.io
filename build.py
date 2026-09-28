import os
import re
import json
import html
import requests
from bs4 import BeautifulSoup
from datetime import datetime

CHANNEL_URL = "https://t.me/s/Deal_Offers_Looto"
DEALS_FILE = "deals.json"
MAX_DEALS = 50

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

def load_existing_deals():
    if os.path.exists(DEALS_FILE):
        try:
            with open(DEALS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_deals(deals):
    with open(DEALS_FILE, "w", encoding="utf-8") as f:
        json.dump(deals, f, ensure_ascii=False, indent=2)

def fetch_telegram_deals():
    try:
        res = requests.get(CHANNEL_URL, headers=headers, timeout=15)
        if res.status_code != 200:
            print("Failed to fetch channel page")
            return []
        
        soup = BeautifulSoup(res.text, "html.parser")
        messages = soup.find_all("div", class_="tgme_widget_message")
        parsed_deals = []

        for msg in messages:
            post_id = msg.get("data-post", "")
            
            # Photo extract
            photo_tag = msg.find("a", class_="tgme_widget_message_photo_wrap")
            image_url = None
            if photo_tag and "style" in photo_tag.attrs:
                style = photo_tag["style"]
                match = re.search(r"background-image:url\('?(.*?)'?\)", style)
                if match:
                    image_url = match.group(1)

            # Text extract
            text_div = msg.find("div", class_="tgme_widget_message_text")
            if not text_div:
                continue

            raw_html = text_div.decode_contents()
            clean_text = text_div.get_text(separator="\n").strip()

            # Find first link for button
            first_link = None
            for a in text_div.find_all("a", href=True):
                href = a["href"]
                if "t.me" not in href:
                    first_link = href
                    break
            
            if not first_link:
                first_link = f"https://t.me/{post_id}"

            parsed_deals.append({
                "id": post_id,
                "image": image_url,
                "html": raw_html,
                "text": clean_text[:120] + "..." if len(clean_text) > 120 else clean_text,
                "link": first_link,
                "time": datetime.utcnow().strftime("%d %b, %I:%M %p")
            })

        return parsed_deals
    except Exception as e:
        print("Fetch error:", e)
        return []

def generate_html(deals):
    schema_items = []
    cards_html = ""

    for idx, deal in enumerate(deals):
        # Google Schema item
        schema_items.append({
            "@type": "ListItem",
            "position": idx + 1,
            "item": {
                "@type": "Product",
                "name": deal["text"].replace('"', '').replace('\n', ' ')[:80],
                "image": deal["image"] or "https://via.placeholder.com/300x200?text=Loot+Deal",
                "offers": {
                    "@type": "Offer",
                    "url": deal["link"],
                    "priceCurrency": "INR",
                    "availability": "https://schema.org/InStock"
                }
            }
        })

        # Card HTML
        img_tag = f'<img src="{deal["image"]}" alt="Loot Deal" loading="lazy" class="card-img">' if deal["image"] else '<div class="no-img">🔥 LOOT DEAL</div>'
        cards_html += f"""
        <div class="deal-card">
            {img_tag}
            <div class="card-body">
                <span class="badge">LIVE OFFER</span>
                <div class="card-text">{deal["html"]}</div>
                <div class="card-footer">
                    <span class="time">{deal["time"]}</span>
                    <a href="{deal["link"]}" target="_blank" rel="nofollow noopener" class="buy-btn">Grab Deal 🚀</a>
                </div>
            </div>
        </div>
        """

    schema_json = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Live Loot Deals & Online Shopping Discounts",
        "itemListElement": schema_items
    }, ensure_ascii=False)

    full_html = f"""<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deal Offers Looto - Top 50 Live Loot Deals & Discounts</title>
    <meta name="description" content="आज की सबसे सस्ती लूट डील्स, भारी डिस्काउंट और कूपन कोड्स। Amazon, Flipkart, Myntra की टॉप लाइव डील्स।">
    <link rel="canonical" href="https://paisablueprinthindi-sketch.github.io/">
    <script type="application/ld+json">
    {schema_json}
    </script>
    <style>
        :root {{ --primary: #ff4757; --dark: #1e293b; --light: #f8fafc; --text: #334155; }}
        * {{ margin:0; padding:0; box-sizing:border-box; font-family: system-ui, -apple-system, sans-serif; }}
        body {{ background: var(--light); color: var(--text); padding-bottom: 50px; }}
        header {{ background: var(--dark); color: #fff; padding: 20px; text-align: center; border-bottom: 4px solid var(--primary); }}
        header h1 {{ font-size: 1.8rem; margin-bottom: 5px; color: #fff; }}
        .header-sub {{ font-size: 0.95rem; color: #94a3b8; }}
        .banner {{ background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 15px; text-align: center; font-weight: bold; margin: 15px auto; max-width: 1100px; border-radius: 12px; }}
        .banner a {{ color: #ffeb3b; text-decoration: underline; margin-left: 8px; font-size: 1.05rem; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 15px; display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }}
        .deal-card {{ background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); display: flex; flex-direction: column; transition: transform 0.2s; border: 1px solid #e2e8f0; }}
        .deal-card:hover {{ transform: translateY(-3px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }}
        .card-img {{ width: 100%; height: 200px; object-fit: cover; background: #e2e8f0; }}
        .no-img {{ width: 100%; height: 120px; background: #fee2e2; color: var(--primary); display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.2rem; }}
        .card-body {{ padding: 15px; display: flex; flex-direction: column; flex-grow: 1; }}
        .badge {{ background: #fee2e2; color: #dc2626; font-size: 0.75rem; padding: 3px 8px; border-radius: 20px; font-weight: bold; align-self: flex-start; margin-bottom: 8px; }}
        .card-text {{ font-size: 0.9rem; line-height: 1.4; color: #1e293b; margin-bottom: 15px; flex-grow: 1; word-break: break-word; }}
        .card-text a {{ color: #2563eb; text-decoration: none; font-weight: 500; }}
        .card-footer {{ display: flex; align-items: center; justify-content: space-between; border-top: 1px solid #f1f5f9; padding-top: 10px; }}
        .time {{ font-size: 0.75rem; color: #94a3b8; }}
        .buy-btn {{ background: var(--primary); color: #fff; text-decoration: none; padding: 8px 16px; border-radius: 8px; font-weight: bold; font-size: 0.85rem; }}
        .buy-btn:hover {{ background: #ee5253; }}
        footer {{ text-align: center; margin-top: 40px; color: #64748b; font-size: 0.85rem; }}
    </style>
</head>
<body>
    <header>
        <h1>🔥 Deal Offers Looto</h1>
        <p class="header-sub">भारत की ताज़ा लूट डील्स व ऑफर्स (Rolling 50 Live Updates)</p>
    </header>

    <div class="banner">
        🎁 ऑनलाइन शॉपिंग पर ₹5,000 की बचत के लिए CashKaro जॉइन करें! 
        <a href="https://cashk.app.link/vu5M0Y40L6b" target="_blank" rel="nofollow">Claim Cashback 👉</a>
    </div>

    <main class="container">
        {cards_html}
    </main>

    <footer>
        <p>© 2026 Deal Offers Looto • All deals automatically synced from Telegram.</p>
    </footer>
</body>
</html>"""
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)
    print("✅ index.html with Schema generated successfully!")

def main():
    existing_deals = load_existing_deals()
    fresh_deals = fetch_telegram_deals()

    # Merge fresh with existing based on ID
    existing_ids = {d["id"] for d in existing_deals}
    new_additions = [d for d in fresh_deals if d["id"] not in existing_ids]

    # Combined with newest first
    all_deals = new_additions + existing_deals
    rolling_50 = all_deals[:MAX_DEALS]

    save_deals(rolling_50)
    generate_html(rolling_50)

if __name__ == "__main__":
    main()
