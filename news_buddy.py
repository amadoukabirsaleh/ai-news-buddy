""" AI News Buddy fetches, summarizes, and delivers daily news via Telegram"""

import os 
from datetime import datetime, time, timedelta, timezone

import feedparser
import requests
from google import genai
from google.genai import types, errors


from config import FEEDS, TELEGRAM_MESSAGE_LIMIT, MAX_ARTICLES_PER_DOMAIN, TOTAL_TARGET_CHARS

def load_env():
    """Load environment variables from .env file if it exists"""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())



def fetch_feeds():
    """Fetch articles from all configured RSS feeds, filtered to last week."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=168)
    articles = []

    for domain, urls in FEEDS.items():
        for url in urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:MAX_ARTICLES_PER_DOMAIN]:
                    published = entry.get("published_parsed")
                    if published:
                        pub_dt = datetime(*published[:6], tzinfo=timezone.utc)
                        if pub_dt < cutoff:
                            continue

                    articles.append({
                        "title": entry.get("title", "No title"),
                        "summary": entry.get("summary", "")[:300],
                        "link": entry.get("link", ""),
                        "domain": domain,
                    })
            except Exception as e:
                print(f"Error fetching {url}: {e}")

    return articles


def summarize(articles):
    """Send articles to Gemini and get a friend-like summary"""

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


    # gemini-2.5-flash-lite is highly optimized, fast and much less prone to 503 congestion

    selected_model = "gemini-3.5-flash-lite"

    max_retries = 3
    retry_delay = 5

    # If there is no articles
    if not articles:
        prompt = (
            "Hey, there is no major news in my feeds today. "
            "Write me a highly engaging, conversational, 1-paragraph friendly message focusing on my PhD domain: "
            "Prognosis and Health Management (PHM) for workstations and enterprise PCs. "
            "Teach me something interesting today about this domain. For example: "
            "1. A market insight, statistic, or competitor comparison regarding top DEX (Digital Employee Experience) tools "
            "like Nexthing, Microsoft Intune, 1E, or Lakeside. "
            "2. A cool scientific method or approach for analyzing system logs, hardware metrics, or IT ticket data to predict or diagnose crashes. "
            "Make it highly practical so I can learn something new and even talk about it with my colleagues at lunch. "
            "I am a French speaker, so your response must be entirely in French."
        )
        for attempt in range(max_retries):
            try:

                response = client.models.generate_content(
                model=selected_model,
                contents=f"Here are today's news articles to summarize:\n\n{articles_text}",
                config=types.GenerateContentConfig(
                    system_instruction=prompt,
                    max_output_tokens=1000,
                    temperature=0.9,
                ),
                )

                return response.text
            except errors.APIError as e:
                if e.code == 503 and attempt<max_retries:
                     print(f"⚠️ Google's servers are busy (503). Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                     time.sleep(retry_delay)
                     continue
                raise e
    # There exist articles fecthed
    articles_text = ""

    for article in articles:
        articles_text += f"[{article['domain']}] {article['title']}\n{article['summary']}\n\n"


    system_instruction = """
        You are my personal technology scout and intellectually curious friend.

        Your mission is NOT to write a news digest. Every morning, send me one short Telegram message that makes me feel I discovered something worth knowing, thinking about, or discussing with a colleague.

        ABOUT ME
        I am a PhD researcher in Prognostics and Health Management (PHM) for enterprise workstations. My interests include AI/ML, predictive maintenance, Windows telemetry, log analysis, root cause analysis, incident management, observability, Digital Employee Experience (DEX), emerging technology, and European AI developments.

        However, when presenting me with the news, consider me as a beginner, and make sure the news is not complicated to understand
        EDITORIAL SELECTION
        - Examine the available articles and identify the strongest stories from the last 7 days, prioritizing the last 72 hours.
        - Select at most TWO news stories, based on novelty, concrete evidence, technical importance, or surprising consequences.
        - Do not force coverage of every topic. Quality beats quantity.
        - Prioritize original research, official announcements, technical documentation, and trustworthy reporting.
        - Never invent dates, numbers, quotations, research findings, or sources.       
        - Start with a casual greeting that varies each day.
        - End with something encouraging or a fun sign-off.

        THE DAILY GEM
        Always include ONE memorable educational insight relevant to my PhD or adjacent technical knowledge.
        Choose a specific mechanism, counterintuitive observation, scientific technique, engineering trade-off, or failure mode.
        Explain HOW it works with a concrete miniature example whenever possible.
        Finish with one thought-provoking question or observation that follows from the technical explanation. Avoid generic motivational quotes.
        Rotate the subject across PHM, Windows internals, time series, anomaly detection, log mining, RCA, causal inference, incident response, DEX, and scientific methodology.
        The gem does not need to be recent, but it must be accurate.

        WRITING STYLE
        - Write exclusively in natural, contemporary conversational French.
        - Sound like a knowledgeable friend sharing a fascinating discovery, not a journalist, consultant, professor, or motivational speaker.
        - Start directly with the interesting detail. Do not waste space setting the scene.
        - For each news story, explain WHAT happened, ONE important detail, and WHY it matters.
        - Prefer concrete examples and mechanisms over abstract generalizations.
        - Use short flowing paragraphs and natural transitions, without formal headings or bullet lists.
        - Be curious, warm, direct, and occasionally playful, but never use forced slang or artificial hype.
        - Use no more than two emojis, and only when they feel natural.
        - Never use empty claims such as "l'IA révolutionne le monde", "à suivre de près", or "cela change la donne" without evidence.
        - Use short sentences, clear and simple.

        OUTPUT
        - Target 1000–1100 French characters, maximum 1500.
        - Usually two news stories plus the daily gem; use fewer stories if quality is weak.
        - Make it feel like ONE friendly Telegram message, not a newsletter.
        - Put source links discreetly at the end.
        - Silently check: Is this specific? Is it true? Did I learn something? Will I remember an idea tonight?
        - Return only the Telegram message.
        """
        


                  
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=selected_model,
                contents=f"Here are today's news articles to summarize:\n\n{articles_text}",
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    max_output_tokens=1000,
                    temperature=0.9,
                ),
                )

            return response.text
        except errors.APIError as e:
            if e.code == 503 and attempt<max_retries:
                    print(f"⚠️ Google's servers are busy (503). Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
            raise e 


def send_telegram(message):
    """Send a message via Telegram Bot API."""

    token = os.environ["TELEGRAM_BOT_TOKEN"].strip()
    chat_id = os.environ["TELEGRAM_CHAT_ID"].strip()

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    

    # Split message if it exceeds Telegram limit

    if len(message) <= TELEGRAM_MESSAGE_LIMIT:
        chunks = [message]
    else:
        chunks = [message[i:i+TELEGRAM_MESSAGE_LIMIT] for i in range(0, len(message), TELEGRAM_MESSAGE_LIMIT)]


    for chunk in chunks:
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "Markdown",
        }

        resp = requests.post(url, json=payload)

        if resp.status_code != 200:
            payload["parse_mode"]= ""
            resp = requests.post(url, json=payload)

        resp.raise_for_status()


"""Main pipeline: fetch, summarize, send."""

def main():
    """Main pipeline: fetch, summarize, print"""
    load_env()
    print("Fetching feeds...")
    articles = fetch_feeds()
    print(f"Found {len(articles)} articles")

    print("Summarizing with Gemini...")
    message = summarize(articles)
    print(f"Message ({len(message)} chars:)")
    print(message)

    print("Sending to Telegram...")
    send_telegram(message)
    print("Done!")

if __name__ == "__main__":
    main()
