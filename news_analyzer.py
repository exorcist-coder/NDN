import streamlit as st
import requests
from datetime import datetime, timedelta
import google.generativeai as genai
from textblob import TextBlob
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="📰 News Analyzer Pro",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .main-header { font-size: 2.5em; color: #1f77b4; margin-bottom: 10px; }
    .card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin: 10px 0; }
    .high-credibility { color: #28a745; font-weight: bold; }
    .low-credibility { color: #dc3545; font-weight: bold; }
    .neutral-credibility { color: #ffc107; font-weight: bold; }
    .positive-sentiment { color: #28a745; }
    .negative-sentiment { color: #dc3545; }
    .neutral-sentiment { color: #6c757d; }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for caching
if 'articles_cache' not in st.session_state:
    st.session_state.articles_cache = None
if 'cache_time' not in st.session_state:
    st.session_state.cache_time = None

# Configure APIs
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
GEMINI_KEY = os.getenv("GEMINI_KEY", "")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

# Credibility database of known sources
CREDIBILITY_SCORES = {
    "bbc": 95, "reuters": 94, "ap news": 93, "cnn": 85, "bbc news": 95,
    "guardian": 88, "new york times": 87, "nyt": 87, "washington post": 86,
    "financial times": 85, "the times": 84, "independent": 82, "telegraph": 80,
    "politico": 78, "cnbc": 80, "business insider": 75, "medium": 40,
    "twitter": 35, "reddit": 30, "unknown": 50
}

def get_credibility_score(source, content):
    """Calculate credibility score based on source and content"""
    # Base score from source
    source_lower = source.lower()
    base_score = CREDIBILITY_SCORES.get("unknown", 50)
    
    for known_source, score in CREDIBILITY_SCORES.items():
        if known_source in source_lower:
            base_score = score
            break
    
    # Content quality adjustments
    exclamation_count = content.count("!")
    caps_words = len([w for w in content.split() if w.isupper() and len(w) > 1])
    
    # Penalize sensationalism
    if exclamation_count > 3:
        base_score -= 10
    if caps_words > 5:
        base_score -= 5
    
    return max(0, min(100, base_score))

def get_sentiment(text):
    """Analyze sentiment of text"""
    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        
        if polarity > 0.1:
            return "Positive 😊", polarity
        elif polarity < -0.1:
            return "Negative 😢", polarity
        else:
            return "Neutral 😐", polarity
    except:
        return "Neutral 😐", 0

def summarize_with_gemini(content, title):
    """Use Gemini to summarize article"""
    if not GEMINI_KEY:
        return "API key not configured. Please set GEMINI_KEY environment variable."
    
    try:
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"""Summarize this news article in 1-2 sentences. Be concise and factual.

Title: {title}

Content: {content[:2000]}

Summary:"""
        
        response = model.generate_content(prompt, stream=False)
        return response.text.strip()
    except Exception as e:
        return f"Could not summarize: {str(e)}"

def fetch_news(query, days=7):
    """Fetch news from NewsAPI"""
    if not NEWSAPI_KEY:
        st.error("❌ NewsAPI key not found! Please set NEWSAPI_KEY environment variable.")
        return None
    
    try:
        from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "from": from_date,
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": 10,
            "apiKey": NEWSAPI_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data["status"] == "ok":
            return data["articles"]
        else:
            st.error(f"API Error: {data.get('message', 'Unknown error')}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Network error: {str(e)}")
        return None

def process_articles(articles, summarize=True):
    """Process articles with summaries and credibility scores"""
    processed = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, article in enumerate(articles):
        status_text.text(f"Processing article {idx+1}/{len(articles)}...")
        
        title = article.get("title", "N/A")
        source = article.get("source", {}).get("name", "Unknown")
        content = article.get("description", "") + " " + article.get("content", "")
        image = article.get("urlToImage", "")
        url = article.get("url", "")
        published = article.get("publishedAt", "N/A")
        
        # Calculate credibility
        credibility = get_credibility_score(source, content)
        
        # Get sentiment
        sentiment, polarity = get_sentiment(content)
        
        # Summarize (optional)
        summary = ""
        if summarize and GEMINI_KEY:
            summary = summarize_with_gemini(content, title)
        else:
            summary = (article.get("description", "No summary available")[:200] + "...")
        
        processed.append({
            "title": title,
            "source": source,
            "credibility": credibility,
            "sentiment": sentiment,
            "polarity": polarity,
            "summary": summary,
            "image": image,
            "url": url,
            "published": published
        })
        
        progress_bar.progress((idx + 1) / len(articles))
    
    progress_bar.empty()
    status_text.empty()
    
    return processed

def display_article_card(article, index):
    """Display individual article card"""
    # Credibility color coding
    if article["credibility"] >= 80:
        cred_color = "high-credibility"
        cred_icon = "✅"
    elif article["credibility"] >= 60:
        cred_color = "neutral-credibility"
        cred_icon = "⚠️"
    else:
        cred_color = "low-credibility"
        cred_icon = "❌"
    
    # Sentiment color coding
    if "Positive" in article["sentiment"]:
        sent_color = "positive-sentiment"
    elif "Negative" in article["sentiment"]:
        sent_color = "negative-sentiment"
    else:
        sent_color = "neutral-sentiment"
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if article["image"]:
            st.image(article["image"], use_column_width=True)
    
    with col2:
        st.markdown(f"### {article['title']}")
        st.markdown(f"**Source:** {article['source']} | **Published:** {article['published'][:10]}")
        
        # Metrics row
        metric_cols = st.columns(3)
        with metric_cols[0]:
            st.markdown(f"<p class='{cred_color}'>Credibility: {article['credibility']}% {cred_icon}</p>", unsafe_allow_html=True)
        with metric_cols[1]:
            st.markdown(f"<p class='{sent_color}'>Sentiment: {article['sentiment']}</p>", unsafe_allow_html=True)
        
        st.markdown(f"**Summary:** {article['summary']}")
        st.markdown(f"[Read Full Article →]({article['url']})")
    
    st.divider()

# =====================
# MAIN APP
# =====================

st.markdown('<h1 class="main-header">📰 Automated News Summarizer & Fake News Detector</h1>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    search_query = st.text_input(
        "🔍 What news are you interested in?",
        placeholder="e.g., Tesla, Bitcoin, Artificial Intelligence, Climate Change...",
        value="technology"
    )

with col2:
    days_back = st.selectbox("📅 Time range:", [1, 3, 7, 30], index=2)

col1, col2, col3 = st.columns(3)
with col1:
    use_summaries = st.checkbox("✨ Generate AI Summaries", value=True, help="Uses Gemini API (slower but better)")
with col2:
    sort_by = st.selectbox("Sort by:", ["Credibility (High→Low)", "Date (Newest)", "Sentiment"], index=0)
with col3:
    if st.button("🚀 Fetch & Analyze News", type="primary"):
        st.session_state.force_refresh = True

st.divider()

# Fetch and process
if search_query:
    # Check if we need to fetch new data
    should_fetch = True
    if st.session_state.articles_cache and st.session_state.cache_time:
        time_diff = time.time() - st.session_state.cache_time
        if time_diff < 300:  # Cache for 5 minutes
            should_fetch = False
    
    if st.session_state.get('force_refresh', False) or should_fetch:
        with st.spinner(f"🔄 Fetching news about '{search_query}'..."):
            articles = fetch_news(search_query, days=days_back)
        
        if articles:
            st.session_state.articles_cache = articles
            st.session_state.cache_time = time.time()
            st.session_state.force_refresh = False
        else:
            articles = None
    else:
        articles = st.session_state.articles_cache
    
    if articles:
        with st.spinner("⏳ Processing articles..."):
            processed = process_articles(articles, summarize=use_summaries)
        
        # Sort articles
        if sort_by == "Credibility (High→Low)":
            processed.sort(key=lambda x: x["credibility"], reverse=True)
        elif sort_by == "Date (Newest)":
            processed.sort(key=lambda x: x["published"], reverse=True)
        elif sort_by == "Sentiment":
            processed.sort(key=lambda x: x["polarity"], reverse=True)
        
        # Statistics
        st.subheader("📊 Analysis Overview")
        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
        
        avg_credibility = sum(a["credibility"] for a in processed) / len(processed)
        positive_count = sum(1 for a in processed if "Positive" in a["sentiment"])
        negative_count = sum(1 for a in processed if "Negative" in a["sentiment"])
        neutral_count = len(processed) - positive_count - negative_count
        
        with stats_col1:
            st.metric("📈 Articles Analyzed", len(processed))
        with stats_col2:
            st.metric("🎯 Avg Credibility", f"{avg_credibility:.0f}%")
        with stats_col3:
            st.metric("😊 Positive Sentiment", f"{positive_count}/{len(processed)}")
        with stats_col4:
            st.metric("😢 Negative Sentiment", f"{negative_count}/{len(processed)}")
        
        st.divider()
        
        # Display articles
        st.subheader("📰 Analyzed Articles")
        for idx, article in enumerate(processed, 1):
            with st.expander(f"{idx}. {article['title'][:80]}..."):
                display_article_card(article, idx)

else:
    st.info("👈 Enter a search query above to get started!")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
💡 <b>How This Works:</b> This tool fetches real news articles, analyzes their credibility based on source reputation and language patterns, 
generates AI summaries, and detects emotional sentiment. Always cross-reference with official sources!

🔐 <b>Privacy:</b> Your searches are not stored. All processing happens in real-time.
</div>
""", unsafe_allow_html=True)
