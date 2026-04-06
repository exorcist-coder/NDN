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
    page_title="📰 News Analyzer",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS theme
st.markdown("""
    <style>
    .main-header { 
        font-size: 2.8em; 
        color: #00d4ff; 
        margin-bottom: 5px;
        font-weight: bold;
        letter-spacing: 1px;
    }
    .subtitle {
        font-size: 0.9em;
        color: #888;
        margin-bottom: 20px;
    }
    .tier1 { color: #28a745; font-weight: bold; }
    .tier2 { color: #ffc107; font-weight: bold; }
    .tier3 { color: #ff9800; font-weight: bold; }
    .unreliable { color: #dc3545; font-weight: bold; }
    .card { 
        background-color: white; 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 4px solid #00d4ff;
        margin: 15px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .credibility-badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9em;
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
        return "tier1", 93, "#28a745"
    elif any(tier2 in source_lower for tier2 in TIER_2_SOURCES):
        return "tier2", 78, "#ffc107"
    elif any(tier3 in source_lower for tier3 in TIER_3_SOURCES):
        return "tier3", 65, "#ff9800"
    elif any(unreliable in source_lower for unreliable in UNRELIABLE_SOURCES):
        return "unreliable", 35, "#dc3545"
    else:
        return "unknown", 55, "#6c757d"

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
    """Get color gradient based on credibility score (red to green)"""
    score = max(0, min(100, score))  # Ensure between 0-100
    
    if score < 20:
        return "#dc3545"  # Dark red
    elif score < 40:
        return "#ff6b6b"  # Red
    elif score < 50:
        return "#ff9800"  # Orange
    elif score < 60:
        return "#ffc107"  # Yellow
    elif score < 75:
        return "#58b368"  # Light green
    elif score < 90:
        return "#28a745"  # Green
    else:
        return "#1e7e34"  # Dark green

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
    """Display individual article card with professional styling and thumbnail"""
    cred = article["credibility"]
    color = article["color"]
    image = article.get("image", "")
    
    # Build image HTML if available
    image_html = ""
    if image and image.strip():
        image_html = f"""
        <img src="{image}" style="
            width: 100%;
            height: 250px;
            object-fit: cover;
            border-radius: 8px 8px 0 0;
            display: block;
            margin-bottom: 15px;
        " onerror="this.style.display='none';" alt="Article thumbnail">
        """
    
    st.markdown(f"""
    <div class="card" style="border-left-color: {color}; overflow: hidden;">
        {image_html}
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
            <h3 style="margin: 0; color: #1a1a1a; flex: 1; line-height: 1.3;">{article['title']}</h3>
            <span class="credibility-badge" style="background-color: {color}; color: white; flex-shrink: 0; margin-left: 10px;">
                {cred}%
            </span>
        </div>
        <p style="color: #666; margin: 8px 0; font-size: 0.85em; line-height: 1.4;">
            📰 <strong>{article['source']}</strong> | 📅 {article['published'][:10]} | {article['sentiment']}
        </p>
        <p style="color: #333; line-height: 1.6; margin: 12px 0; font-size: 0.95em;">
            {article['summary']}
        </p>
        <a href="{article['url']}" target="_blank" style="
            display: inline-block;
            padding: 10px 18px;
            background-color: {color};
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-weight: bold;
            margin-top: 10px;
            font-size: 0.9em;
            transition: opacity 0.2s;
        " onmouseover="this.style.opacity='0.85'" onmouseout="this.style.opacity='1'">
            → Read Full Article
        </a>
    </div>
    """, unsafe_allow_html=True)

# =====================
# MAIN APP
# =====================

st.markdown('<h1 class="main-header">📰 NEWS ANALYZER</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Real-time Credibility Scoring | Sentiment Analysis | AI Summaries | Fact-Based Journalism</p>', unsafe_allow_html=True)

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
        with st.spinner("⏳ Analyzing articles..."):
            processed = process_articles(articles, use_gemini=use_gemini)
        
        # Sort articles
        if sort_by == "Credibility ↓":
            processed.sort(key=lambda x: x["credibility"], reverse=True)
        elif sort_by == "Latest":
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
            st.metric("📈 Articles", len(processed))
        with stats_col2:
            st.metric("🎯 Avg Credibility", f"{avg_credibility:.0f}%")
        with stats_col3:
            st.metric("😊 Positive", f"{positive_count}/{len(processed)}")
        with stats_col4:
            st.metric("😢 Negative", f"{negative_count}/{len(processed)}")
        
        st.divider()
        
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
