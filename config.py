"""RSS feed configuration organized by domain."""

FEEDS = {
    "ai_general": [
        "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en",
        "https://www.technologyreview.com/feed/",
        "https://openai.com/blog/rss.xml",
    ],
    "log_analysis": [
        "https://rss.arxiv.org/rss/cs.SE",
        "https://rss.arxiv.org/rss/cs.LG",
        "https://www.elastic.co/blog/feed",
        "https://www.honeycomb.io/blog/rss.xml",
    ],
    "incident_diagnosis": [
        "https://rss.arxiv.org/rss/cs.DC",
        "https://rss.arxiv.org/rss/cs.NI",
        "https://sreweekly.com/feed/",
        "https://incident.io/blog/feed.xml",
    ],
    "ai_europe": [
        "https://news.google.com/rss/search?q=intelligence+artificielle+France&hl=fr&gl=FR&ceid=FR:fr",
    ],
}

TELEGRAM_MESSAGE_LIMIT = 4096
MAX_ARTICLES_PER_DOMAIN = 5
TOTAL_TARGET_CHARS = 3000