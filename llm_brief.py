from groq import Groq
import json
from datetime import date
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def get_market_context(client):
    """Fetch live energy market headlines via NewsAPI"""
    print("Fetching live market context...")
    try:
        import requests
        news_key = os.getenv("NEWS_API_KEY")
        if not news_key:
            raise ValueError("No NEWS_API_KEY in .env")

        queries = ["European gas TTF", "EU ETS carbon price", "European power price"]
        articles_seen = {} 

        for q in queries:
            r = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": q,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": 3,
                    "apiKey": news_key
                },
                timeout=10
            )
            for a in r.json().get("articles", []):
                title = a["title"]
                if title not in articles_seen:
                    articles_seen[title] = {
                        "date": a["publishedAt"][:10],
                        "title": title,
                        "source": a["source"]["name"],
                        "url": a.get("url", "")
                    }

        top_articles = list(articles_seen.values())[:9]

        context_for_llm = "\n".join([
            f"[{i+1}] {a['date']} | {a['source']}: {a['title']}"
            for i, a in enumerate(top_articles)
        ])

        print(f"  Fetched {len(top_articles)} headlines")
        return context_for_llm, top_articles

    except Exception as e:
        print(f"  News fetch failed ({e}) - metrics only mode")
        return "", []


def generate_brief(metrics):
    """Call Groq API to generate a trading brief from live metrics + live context"""

    metrics_text = "\n".join([
        f"- {m['metric']}: {m['value']} {m['unit']}"
        for m in metrics
    ])


    m_dict = {m["metric"]: m["value"] for m in metrics}
    ttf = m_dict.get("TTF Front-Month", "N/A")
    storage = m_dict.get("EU Gas Storage Fill", "N/A")
    eua = m_dict.get("EU ETS Carbon (EUA)", "N/A")
    spread = m_dict.get("Clean Spark Spread", "N/A")
    power = m_dict.get("German Power DA", "N/A")
    lng = m_dict.get("EU LNG Send-Out", "N/A")

    client = Groq(api_key=GROQ_API_KEY)
    market_context, articles = get_market_context(client)

    if market_context:
        context_section = f"""Latest market news (auto-fetched today, cite by number [1]-[9]):
{market_context}"""
    else:
        context_section = "Note: Live news unavailable - base analysis on metrics only."

    prompt = f"""You are a senior European energy market analyst writing a morning brief for a gas and power trading desk.

Today is {date.today().strftime('%d %B %Y')}.

Today's live market metrics:
{metrics_text}

{context_section}

Write a concise 180-220 word trading brief in flowing prose (no bullet points). Structure it as follows:

PARAGRAPH 1 - THE SO WHAT (lead with the key risk or opportunity, then back it up with numbers):
Start with the single most important thing a trader needs to know this morning. State it as a clear directional view, then immediately support it with the relevant metrics. Do not open by listing the metrics — open with the insight.

PARAGRAPH 2 - CARBON & POWER CURVE:
Assess EUA at {eua} EUR/t and what it adds to generation cost (use 0.202 t/MWh emission factor). Explain what the spark spread of {spread} EUR/MWh implies for merit order and whether German DA at {power} EUR/MWh is consistent with fundamentals or looks mispriced.

PARAGRAPH 3 - KEY RISK & TRADE IDEA:
Name one specific risk to watch today with a directional implication (e.g. if X happens, TTF moves Y).

Be direct, quantitative, and decision-useful. Do not invent causal relationships between metrics that are not directly linked. Write like a trader, not an academic."""

    print("Generating trading brief...")
    print(f"\n--- PROMPT SENT TO LLM ---\n{prompt}\n--------------------------\n")

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6, 
        max_tokens=1024
    )

    brief_body = completion.choices[0].message.content

    full_brief = brief_body

    print("--- LLM OUTPUT ---")
    print(full_brief)
    print("------------------\n")

    log = {
        "date": str(date.today()),
        "market_context": market_context,
        "articles": articles,
        "prompt": prompt,
        "output": full_brief,
        "model": "llama-3.3-70b-versatile",
        "input_tokens": completion.usage.prompt_tokens,
        "output_tokens": completion.usage.completion_tokens
    }

    os.makedirs("output", exist_ok=True)
    with open("output/llm_log.json", "w") as f:
        json.dump(log, f, indent=2)

    print("Logged to output/llm_log.json")
    return full_brief


if __name__ == "__main__":
    from data_ingestion import get_all_metrics
    metrics = get_all_metrics()
    generate_brief(metrics)