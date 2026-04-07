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
# News API
NEWS_API_KEY=97d1ce085bfd40baa38cee73971a7450

# Gemini API
GEMINI_API_KEY=AIzaSyCUu2iDqhoacvHPF3iUctQrLs-iKBVyWGs

# Set page config
st.set_page_config(
    page_title="📰 News Analyzer",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Discord-inspired CSS theme
st.markdown("""
    <style>
    body { 
        background-color: #1e1e1e !important;
        color: #e8ecf1;
    }
    .main {
        background-color: #1e1e1e;
    }
    .stApp {
        background-color: #1e1e1e;
    }
    .main-header { 
        font-size: 1.6em !important; 
        color: #ffffff !important; 
        margin-bottom: -8px !important;
        margin-top: -16px !important;
        padding: 0 !important;
        font-weight: 900 !important;
        letter-spacing: 1px;
        text-shadow: 0 2px 12px rgba(88, 020, 8, 0);
    }
    .subtitle {
        font-size: 0.7em;
        color: #d5dadf;
        margin-bottom: 4px;
        margin-top: -12px;
        padding: 0;
        letter-spacing: 0.5px;
        font-weight: 500;
    }
    /* Discord-like input fields */
    .stTextInput input {
        background-color: #2c2f33 !important;
        color: #ffffff !important;
        border: 1px solid #202225 !important;
        border-radius: 6px !important;
        padding: 6px 10px !important;
        font-size: 12px !important;
        transition: all 0.2s ease !important;
        height: 28px !important;
        font-weight: 500 !important;
    }
    .stTextInput input:focus {
        background-color: #2c2f33 !important;
        border-color: #5865f2 !important;
        box-shadow: 0 0 8px rgba(88, 101, 242, 0.4) !important;
    }
    .stTextInput input::placeholder {
        color: #a0a8b0 !important;
    }
    /* Discord-like selectbox */
    .stSelectbox [role="button"] {
        background-color: #2c2f33 !important;
        color: #ffffff !important;
        border: 1px solid #202225 !important;
        border-radius: 6px !important;
        padding: 6px 10px !important;
        font-size: 12px !important;
        min-height: 28px !important;
        font-weight: 500 !important;
    }
    .stSelectbox [role="listbox"] {
        background-color: #36393f !important;
        border: 1px solid #202225 !important;
        border-radius: 8px !important;
    }
    .stSelectbox [role="option"] {
        color: #ffffff !important;
        background-color: #2c2f33 !important;
        font-weight: 500 !important;
    }
    .stSelectbox [role="option"]:hover {
        background-color: #5865f2 !important;
        color: white !important;
    }
    /* Discord-like checkbox */
    .stCheckbox {
        padding: 8px 12px;
        background-color: #2c2f33;
        border-radius: 6px;
        border: 1px solid #202225;
        transition: all 0.2s ease;
    }
    .stCheckbox label {
        color: #e1e8ed !important;
    }
    /* Discord-like button */
    .stButton > button {
        background-color: #5865f2 !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 6px 14px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        font-size: 12px !important;
        height: 28px !important;
    }
    .stButton > button:hover {
        background-color: #4752c4 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(88, 101, 242, 0.5) !important;
    }
    .stButton > button:active {
        transform: translateY(0);
    }
    /* Search/Filter container styling */
    .search-panel {
        background: linear-gradient(135deg, #2c2f33 0%, #23262a 100%);
        border: 1px solid #202225;
        border-radius: 8px;
        padding: 8px 10px;
        margin: 0;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
    }
    /* Stats/Metrics styling - Discord embed style */
    .stats-panel {
        background-color: transparent;
        border: none;
        border-radius: 0;
        padding: 0;
        margin: 0;
        box-shadow: none;
    }
    .stMetric {
        background-color: #2c2f33 !important;
        border: 1px solid #202225 !important;
        border-radius: 6px !important;
        padding: 8px 10px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15) !important;
        margin: 2px 0 !important;
    }
    .stMetric [data-testid="metricDelta"] {
        color: #5865f2 !important;
    }
    .stMetric label {
        color: #c8cdd3 !important;
        font-size: 10px !important;
        font-weight: 700 !important;
        margin: 0 !important;
    }
    .stMetric [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 18px !important;
        font-weight: bold !important;
        margin: 2px 0 0 0 !important;
    }
    /* Article cards */
    .tier1 { color: #6ec46d; font-weight: bold; }
    .tier2 { color: #5865f2; font-weight: bold; }
    .tier3 { color: #8b7aa8; font-weight: bold; }
    .unreliable { color: #d97777; font-weight: bold; }
    .card { 
        background: linear-gradient(135deg, #2c2f33 0%, #23262a 100%);
        padding: 12px; 
        border-radius: 8px; 
        border-left: 3px solid #5865f2;
        border: 1px solid #202225;
        margin: 4px 0;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
        transition: all 0.2s ease;
    }
    .card:hover {
        border-color: #5865f2;
        box-shadow: 0 6px 20px rgba(88, 101, 242, 0.2);
    }
    .credibility-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85em;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
    }
    /* Divider styling */
    .stDivider {
        border-top: 1px solid #202225 !important;
        margin: 2px 0 !important;
    }
    /* Subheader styling */
    h2 {
        color: #e1e8ed !important;
        margin-top: 6px !important;
        margin-bottom: 4px !important;
        font-size: 16px !important;
    }
    /* Info boxes */
    .stAlert {
        background-color: #2c2f33 !important;
        border-left: 4px solid #5865f2 !important;
        border-radius: 8px !important;
        color: #e1e8ed !important;
    }
    /* Spinner styling */
    .stSpinner {
        color: #5865f2 !important;
    }
    /* Reduce column gaps */
    [data-testid="column"] {
        gap: 0 !important;
    }
    /* Reduce form spacing */
    .stForm {
        gap: 0 !important;
    }
    /* Reduce container padding */
    .stContainer {
        padding: 0 !important;
    }
    /* Reduce horizontal spacing */
    [data-testid="stVerticalBlockContainer"] {
        gap: 0 !important;
    }
    /* Improve text contrast globally */
    label {
        color: #e8ecf1 !important;
        font-weight: 500;
    }
    p {
        color: #e1e8ed !important;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'articles_cache' not in st.session_state:
    st.session_state.articles_cache = None
if 'cache_time' not in st.session_state:
    st.session_state.cache_time = None

# Configure APIs
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
GEMINI_KEY = os.getenv("GEMINI_KEY", "")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

# Professional 4-tier source credibility system
TIER_1_SOURCES = {  # Tier 1: Major reputable sources (90-95%)
    "bbc", "bbc news", "reuters", "ap news", "associated press", 
    "guardian", "new york times", "nyt", "washington post", 
    "financial times", "the times", "the telegraph", "telegraph", 
    "economist", "nikkei asia", "ft", "wsj", "wall street journal",
    "bbc world", "cnn international"
}

TIER_2_SOURCES = {  # Tier 2: Quality sources (75-85%)
    "cnn", "bbc america", "cnbc", "politico", "politico pro",
    "bloomberg", "reuters news", "vox", "the verge", "techcrunch",
    "wired", "slate", "the atlantic", "time", "newsweek",
    "independent", "the independent", "open democracy"
}

TIER_3_SOURCES = {  # Tier 3: Moderate sources (60-74%)
    "medium", "forbes", "entrepreneur", "business insider",
    "huffpost", "huff post", "mashable", "polygon", "variety",
    "hollywood reporter", "deadline", "tvline"
}

UNRELIABLE_SOURCES = {  # Unreliable (below 50%)
    "twitter", "x", "reddit", "4chan", "tiktok", "instagram"
}

def get_source_tier(source_name):
    """Determine source credibility tier"""
    source_lower = source_name.lower().strip()
    
    if any(tier1 in source_lower for tier1 in TIER_1_SOURCES):
        return "tier1", 93, "#6ec46d"
    elif any(tier2 in source_lower for tier2 in TIER_2_SOURCES):
        return "tier2", 78, "#5b8fc4"
    elif any(tier3 in source_lower for tier3 in TIER_3_SOURCES):
        return "tier3", 65, "#8b7aa8"
    elif any(unreliable in source_lower for unreliable in UNRELIABLE_SOURCES):
        return "unreliable", 35, "#d97777"
    else:
        return "unknown", 55, "#a0a8b0"

def analyze_content_quality(content):
    """Analyze content for quality indicators"""
    if not content or len(content) < 50:
        return -15
    
    score_adjustment = 0
    
    # Check for proper sentence structure
    sentences = [s for s in content.split('.') if len(s.strip()) > 10]
    if len(sentences) < 2:
        score_adjustment -= 10
    elif len(sentences) > 15:
        score_adjustment += 5
    
    # Check for quoted sources
    if '"' in content or "'" in content:
        score_adjustment += 5
    
    # Check for sensationalism
    sensational_words = ["shocking", "unbelievable", "you won't believe", 
                        "doctors hate", "secret", "exposed", "scandal"]
    sensational_count = sum(1 for word in sensational_words if word.lower() in content.lower())
    score_adjustment -= sensational_count * 3
    
    # Check for excessive caps
    caps_words = len([w for w in content.split() if w.isupper() and len(w) > 2])
    if caps_words > 5:
        score_adjustment -= 5
    
    # Check for excessive exclamation marks
    exclamation_count = content.count("!")
    if exclamation_count > 3:
        score_adjustment -= 3
    
    return max(-20, min(20, score_adjustment))

def get_color_by_score(score):
    """Get color gradient based on credibility score (soft red to green)"""
    score = max(0, min(100, score))  # Ensure between 0-100
    
    if score < 20:
        return "#c97171"  # Soft red
    elif score < 40:
        return "#d97777"  # Soft red-orange
    elif score < 50:
        return "#dfa676"  # Soft orange
    elif score < 60:
        return "#d4a574"  # Soft tan
    elif score < 75:
        return "#8b9d6b"  # Soft yellow-green
    elif score < 90:
        return "#6ec46d"  # Soft green
    else:
        return "#5aad5a"  # Dark soft green

def get_credibility_score(source, content):
    """Professional credibility scoring"""
    tier, base_score, _ = get_source_tier(source)
    content_adjustment = analyze_content_quality(content)
    
    final_score = base_score + content_adjustment
    final_score = max(0, min(100, final_score))
    
    # Get color based on final score, not source tier
    color = get_color_by_score(final_score)
    return final_score, color

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
        return None
    
    try:
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"""Summarize this news article in 1-2 sentences. Be concise and factual.

Title: {title}

Content: {content[:2000]}

Summary:"""
        
        response = model.generate_content(prompt, stream=False)
        return response.text.strip()
    except Exception as e:
        return None

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
            "pageSize": 15,
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

def process_articles(articles, use_gemini=True):
    """Process articles with credibility scores and AI summaries"""
    processed = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, article in enumerate(articles):
        status_text.text(f"Processing article {idx+1}/{len(articles)}...")
        
        title = article.get("title", "N/A")
        source = article.get("source", {}).get("name", "Unknown")
        description = article.get("description", "")
        content = article.get("content", "")
        full_content = description + " " + content if description else content
        
        image = article.get("urlToImage", "")
        url = article.get("url", "")
        published = article.get("publishedAt", "N/A")
        
        # Calculate credibility with color coding
        credibility, color = get_credibility_score(source, full_content)
        
        # Get sentiment
        sentiment, polarity = get_sentiment(full_content)
        
        # Use Gemini for summary if enabled
        summary = None
        if use_gemini and GEMINI_KEY:
            summary = summarize_with_gemini(full_content, title)
        
        # Fallback to description
        if not summary:
            summary = description[:200] if description else "No summary available"
        
        processed.append({
            "title": title,
            "source": source,
            "credibility": credibility,
            "color": color,
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

def display_article_card(article):
    """Display individual article card with professional styling"""
    cred = article["credibility"]
    color = article["color"]
    
    st.markdown(f"""
    <div class="card" style="border-left-color: {color};">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 15px;">
            <h3 style="margin: 0; color: #ffffff; font-weight: 700;">{article['title']}</h3>
            <span class="credibility-badge" style="background-color: {color}; color: white;">
                {cred}% CREDIBLE
            </span>
        </div>
        <p style="color: #c8cdd3; margin: 5px 0; font-size: 0.9em; font-weight: 500;">
            📰 <strong>{article['source']}</strong> | 📅 {article['published'][:10]} | {article['sentiment']}
        </p>
        <p style="color: #e1e8ed; line-height: 1.6; margin: 10px 0;">
            {article['summary']}
        </p>
        <a href="{article['url']}" target="_blank" style="
            display: inline-block;
            padding: 8px 16px;
            background-color: {color};
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            margin-top: 10px;
        ">→ Read Full Article</a>
    </div>
    """, unsafe_allow_html=True)

# =====================
# MAIN APP
# =====================

st.markdown('<h1 class="main-header">📰 NEWS ANALYZER</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Real-time Credibility Scoring | Sentiment Analysis | AI Summaries</p>', unsafe_allow_html=True)

# Discord-like search and filter panel
st.markdown('<div class="search-panel">', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    search_query = st.text_input(
        "🔍 Search Topic:",
        placeholder="e.g., Tesla, Bitcoin, Artificial Intelligence, Climate Change...",
        value="Technology"
    )

with col2:
    days_back = st.selectbox("📅 Time range:", [1, 3, 7, 30], index=2)

col1, col2, col3 = st.columns(3)
with col1:
    use_gemini = st.checkbox("✨ AI Summaries (Gemini)", value=True, help="Slower but better summaries")
with col2:
    sort_by = st.selectbox("Sort by:", ["Credibility ↓", "Latest", "Sentiment"], index=0)
with col3:
    if st.button("🚀 FETCH & ANALYZE", type="primary"):
        st.session_state.force_refresh = True

st.markdown('</div>', unsafe_allow_html=True)

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
        with st.spinner("⏳ Analyzing articles..."):
            processed = process_articles(articles, use_gemini=use_gemini)
        
        # Sort articles
        if sort_by == "Credibility ↓":
            processed.sort(key=lambda x: x["credibility"], reverse=True)
        elif sort_by == "Latest":
            processed.sort(key=lambda x: x["published"], reverse=True)
        elif sort_by == "Sentiment":
            processed.sort(key=lambda x: x["polarity"], reverse=True)
        
        # Statistics - Discord embed style
        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
        
        avg_credibility = sum(a["credibility"] for a in processed) / len(processed)
        positive_count = sum(1 for a in processed if "Positive" in a["sentiment"])
        negative_count = sum(1 for a in processed if "Negative" in a["sentiment"])
        neutral_count = len(processed) - positive_count - negative_count
        
        with stats_col1:
            st.metric("📈 Articles Found", len(processed))
        with stats_col2:
            st.metric("🎯 Avg Credibility", f"{avg_credibility:.0f}%")
        with stats_col3:
            st.metric("😊 Positive Tone", f"{positive_count}")
        with stats_col4:
            st.metric("😢 Negative Tone", f"{negative_count}")
        
        # Display articles
        st.subheader("📰 Analyzed Articles")
        for idx, article in enumerate(processed, 1):
            display_article_card(article)

else:
    st.info("👈 Enter a search query to get started!")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
💡 <b>How This Works:</b> Fetches real news, analyzes credibility based on source & content, 
generates AI summaries with Gemini, and detects sentiment. Always verify with official sources!

🔐 <b>Privacy:</b> Searches not stored. Real-time processing only.
</div>
""", unsafe_allow_html=True)
