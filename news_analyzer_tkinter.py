import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests
from datetime import datetime, timedelta
from textblob import TextBlob
import os
from dotenv import load_dotenv
import webbrowser
import re

# Load environment variables
load_dotenv()

# Configure APIs
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")

# Comprehensive credibility database with tier system
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
        return "tier1", 93
    elif any(tier2 in source_lower for tier2 in TIER_2_SOURCES):
        return "tier2", 78
    elif any(tier3 in source_lower for tier3 in TIER_3_SOURCES):
        return "tier3", 65
    elif any(unreliable in source_lower for unreliable in UNRELIABLE_SOURCES):
        return "unreliable", 35
    else:
        return "unknown", 55

def analyze_content_quality(content):
    """Analyze content for quality indicators"""
    if not content or len(content) < 50:
        return -15  # Very short content is suspicious
    
    score_adjustment = 0
    
    # Check for proper sentence structure and length
    sentences = [s for s in content.split('.') if len(s.strip()) > 10]
    if len(sentences) < 2:
        score_adjustment -= 10  # Too few sentences
    elif len(sentences) > 15:
        score_adjustment += 5  # Well-detailed content
    
    # Check for quoted sources
    if '"' in content or "'" in content:
        score_adjustment += 5  # Has quotes/sources
    
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
    tier, base_score = get_source_tier(source)
    content_adjustment = analyze_content_quality(content)
    
    final_score = base_score + content_adjustment
    final_score = max(0, min(100, final_score))
    
    # Get color based on final score
    color = get_color_by_score(final_score)
    return final_score, color

def get_sentiment(text):
    """Analyze sentiment of text"""
    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        
        if polarity > 0.1:
            return "Positive 😊✅"
        elif polarity < -0.1:
            return "Negative 😡❌"
        else:
            return "Neutral 😐"
    except:
        return "Neutral 😐"

def fetch_news(query, days=7):
    """Fetch news from NewsAPI"""
    if not NEWSAPI_KEY:
        return None, "❌ NewsAPI key not found! Please set NEWSAPI_KEY environment variable."
    
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
            return data["articles"], None
        else:
            return None, f"API Error: {data.get('message', 'Unknown error')}"
    except requests.exceptions.RequestException as e:
        return None, f"❌ Network error: {str(e)}"

class NewsAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("News Analyzer | AI-Powered Credibility Intelligence")
        self.root.geometry("1400x950")
        self.root.configure(bg="#0a0f1e")
        
        self.articles = []
        self.current_sort = "credibility"
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup modern, futuristic 2026 UI design"""
        
        # Header - Modern dark gradient effect
        header_frame = tk.Frame(self.root, bg="#0f1729", height=100)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Accent line
        accent_top = tk.Frame(header_frame, bg="", height=3)
        accent_top.pack(fill=tk.X)
        # Create gradient effect with colored frame
        accent_top.configure(bg="#00d9ff")
        
        title_label = tk.Label(header_frame, text="◆ NEWS ANALYZER ◆", 
                              font=("Helvetica", 26, "bold"), bg="#0f1729", fg="#00d9ff")
        title_label.pack(pady=(12, 3))
        
        subtitle = tk.Label(header_frame, text="AI-POWERED CREDIBILITY INTELLIGENCE | REAL-TIME ANALYSIS", 
                           font=("Helvetica", 9), bg="#0f1729", fg="#00ff88")
        subtitle.pack()
        
        # Search Frame - Modern glassmorphism effect
        search_frame = tk.Frame(self.root, bg="#0a0f1e", height=90)
        search_frame.pack(fill=tk.X, padx=0, pady=0)
        search_frame.pack_propagate(False)
        
        inner_search = tk.Frame(search_frame, bg="#0a0f1e")
        inner_search.pack(fill=tk.X, padx=40, pady=15)
        
        tk.Label(inner_search, text="🔍 SEARCH NEWS:", font=("Helvetica", 11, "bold"), 
                bg="#0a0f1e", fg="#00d9ff").pack(side=tk.LEFT, padx=(0, 15))
        
        self.search_entry = tk.Entry(inner_search, font=("Helvetica", 12), width=40, relief=tk.FLAT, 
                                     bg="#1a2332", fg="#00ff88", bd=0, highlightthickness=2, 
                                     highlightbackground="#00d9ff", highlightcolor="#00d9ff", insertbackground="#00d9ff")
        self.search_entry.pack(side=tk.LEFT, padx=(0, 15), ipady=8)
        self.search_entry.insert(0, "Technology")
        
        search_btn = tk.Button(inner_search, text="❯ ANALYZE", command=self.search_news, 
                              bg="#00d9ff", fg="#000", font=("Helvetica", 11, "bold"), 
                              padx=25, pady=7, relief=tk.FLAT, cursor="hand2", 
                              activebackground="#00ff88", activeforeground="#000")
        search_btn.pack(side=tk.LEFT)
        
        # Options frame - Modern controls
        options_frame = tk.Frame(self.root, bg="#0a0f1e", height=60)
        options_frame.pack(fill=tk.X, padx=0, pady=0)
        options_frame.pack_propagate(False)
        
        inner_options = tk.Frame(options_frame, bg="#0a0f1e")
        inner_options.pack(fill=tk.X, padx=40, pady=12)
        
        tk.Label(inner_options, text="SORT BY:", font=("Helvetica", 10, "bold"), 
                bg="#0a0f1e", fg="#00d9ff").pack(side=tk.LEFT, padx=(0, 20))
        
        self.sort_var = tk.StringVar(value="credibility")
        sort_options = [("⚡ CREDIBILITY", "credibility"), ("⏰ LATEST", "date"), ("💭 SENTIMENT", "sentiment")]
        
        for text, value in sort_options:
            rb = tk.Radiobutton(inner_options, text=text, variable=self.sort_var, value=value, 
                               command=lambda v=value: self.sort_articles(v), bg="#0a0f1e", 
                               font=("Helvetica", 10), fg="#00ff88", activebackground="#0a0f1e",
                               activeforeground="#00d9ff", selectcolor="#0a0f1e")
            rb.pack(side=tk.LEFT, padx=(0, 25))
        
        # Articles frame (scrollable)
        articles_frame = tk.Frame(self.root, bg="#0a0f1e")
        articles_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Modern scrollbar styling
        canvas = tk.Canvas(articles_frame, bg="#0a0f1e", highlightthickness=0, bd=0)
        
        # Custom scrollbar style
        scrollbar_style = ttk.Style()
        scrollbar_style.theme_use('clam')
        scrollbar_style.configure('Vertical.TScrollbar', background="#1a2332", troughcolor="#0a0f1e")
        
        scrollbar = ttk.Scrollbar(articles_frame, orient="vertical", command=canvas.yview, style='Vertical.TScrollbar')
        scrollable_frame = tk.Frame(canvas, bg="#0a0f1e")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y", padx=(0, 5))
        
        self.articles_container = scrollable_frame
        
        # Status bar - Futuristic
        status_frame = tk.Frame(self.root, bg="#0f1729", height=40)
        status_frame.pack(fill=tk.X, padx=0, pady=0)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(status_frame, text="▸ Ready. Enter a search term to begin.", 
                                     bg="#0f1729", fg="#00ff88", font=("Helvetica", 9), anchor="w", padx=40, pady=8)
        self.status_label.pack(fill=tk.X)
    
    def search_news(self):
        """Search for news articles"""
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("Input Required", "Please enter a search term")
            return
        
        self.status_label.config(text="▸ ◆ SEARCHING FOR ARTICLES... ◆")
        self.root.update()
        
        thread = threading.Thread(target=self._perform_search, args=(query,))
        thread.daemon = True
        thread.start()
    
    def _perform_search(self, query):
        """Perform search in background thread"""
        articles, error = fetch_news(query)
        
        if error:
            self.root.after(0, lambda: messagebox.showerror("Error", error))
            self.status_label.config(text="▸ ⚠️  ERROR FETCHING NEWS")
            return
        
        if not articles:
            self.root.after(0, lambda: messagebox.showinfo("No Results", "No articles found for this topic"))
            self.status_label.config(text="▸ NO ARTICLES FOUND")
            return
        
        self.articles = []
        for article in articles:
            title = article.get("title", "N/A")
            source = article.get("source", {}).get("name", "Unknown")
            description = article.get("description", "")
            content = article.get("content", "")
            full_content = description + " " + content if description else content
            
            url = article.get("url", "")
            published = article.get("publishedAt", "N/A")[:10]
            
            credibility, color = get_credibility_score(source, full_content)
            sentiment = get_sentiment(full_content)
            
            summary = description[:180] if description else "No summary available"
            
            self.articles.append({
                "title": title,
                "source": source,
                "credibility": credibility,
                "color": color,
                "sentiment": sentiment,
                "summary": summary,
                "url": url,
                "published": published
            })
        
        # Sort by credibility by default
        self.articles.sort(key=lambda x: x["credibility"], reverse=True)
        
        self.root.after(0, self.display_articles)
        self.root.after(0, lambda: self.status_label.config(text=f"▸ ANALYSIS COMPLETE: {len(self.articles)} ARTICLES LOADED | CREDIBILITY SORTED"))
    
    def sort_articles(self, sort_by):
        """Sort articles"""
        if sort_by == "credibility":
            self.articles.sort(key=lambda x: x["credibility"], reverse=True)
            self.status_label.config(text="▸ ARTICLES SORTED BY CREDIBILITY")
        elif sort_by == "sentiment":
            self.articles.sort(key=lambda x: x["sentiment"])
            self.status_label.config(text="▸ ARTICLES SORTED BY SENTIMENT")
        else:  # date
            self.articles.sort(key=lambda x: x["published"], reverse=True)
            self.status_label.config(text="▸ ARTICLES SORTED BY DATE")
        
        self.display_articles()
    
    def display_articles(self):
        """Display articles with modern, futuristic 2026 design"""
        # Clear previous articles
        for widget in self.articles_container.winfo_children():
            widget.destroy()
        
        if not self.articles:
            no_results = tk.Label(self.articles_container, text="◆ NO ARTICLES FOUND ◆", 
                                 font=("Helvetica", 16, "bold"), bg="#0a0f1e", fg="#00d9ff")
            no_results.pack(pady=120)
            return
        
        # Main articles container with modern spacing
        main_container = tk.Frame(self.articles_container, bg="#0a0f1e")
        main_container.pack(fill=tk.BOTH, expand=True, padx=35, pady=25)
        
        for idx, article in enumerate(self.articles, 1):
            # Modern card with gradient border effect
            card_frame = tk.Frame(main_container, bg="#0a0f1e")
            card_frame.pack(fill=tk.X, pady=(0, 28))
            
            # Outer border frame for gradient effect (simulated with colored frame)
            border_frame = tk.Frame(card_frame, bg=article["color"], height=1)
            border_frame.pack(fill=tk.X, pady=(0, 0))
            border_frame.pack_propagate(False)
            
            # Main card content
            content_frame = tk.Frame(card_frame, bg="#1a2332", relief=tk.FLAT, bd=0, padx=1, pady=1)
            content_frame.pack(fill=tk.BOTH, expand=True)
            
            # Inner content with padding
            inner_frame = tk.Frame(content_frame, bg="#0f1729")
            inner_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=18)
            
            # Top row: Credibility badge + metadata
            top_row = tk.Frame(inner_frame, bg="#0f1729")
            top_row.pack(fill=tk.X, pady=(0, 12))
            
            cred = article["credibility"]
            cred_badge = tk.Label(top_row, text=f"◆ {cred}% CREDIBLE ◆", 
                                 font=("Helvetica", 10, "bold"), bg="#0f1729", fg=article["color"])
            cred_badge.pack(anchor="e", pady=(0, 4))
            
            # Meta info
            meta_frame = tk.Frame(inner_frame, bg="#0f1729")
            meta_frame.pack(fill=tk.X, pady=(0, 12))
            
            source_label = tk.Label(meta_frame, text=f"SOURCE: {article['source'].upper()}", 
                                   font=("Helvetica", 9, "bold"), fg="#00ff88", bg="#0f1729")
            source_label.pack(side=tk.LEFT, padx=(0, 20))
            
            date_label = tk.Label(meta_frame, text=f"DATE: {article['published']}", 
                                 font=("Helvetica", 9), fg="#00d9ff", bg="#0f1729")
            date_label.pack(side=tk.LEFT, padx=(0, 20))
            
            sentiment_label = tk.Label(meta_frame, text=f"MOOD: {article['sentiment']}", 
                                      font=("Helvetica", 9), fg="#ff00ff", bg="#0f1729")
            sentiment_label.pack(side=tk.LEFT)
            
            # Title - Bold and prominent
            title_label = tk.Label(inner_frame, text=article['title'], 
                                  font=("Helvetica", 13, "bold"), bg="#0f1729", fg="#ffffff",
                                  wraplength=1100, justify=tk.LEFT)
            title_label.pack(anchor="w", pady=(0, 14))
            
            # Summary - Clean text
            summary_label = tk.Label(inner_frame, text=article["summary"], 
                                    font=("Helvetica", 10), bg="#0f1729", fg="#b0b8c8",
                                    wraplength=1100, justify=tk.LEFT)
            summary_label.pack(fill=tk.X, pady=(0, 16))
            
            # Action button - Modern
            link_button = tk.Button(inner_frame, text="► READ ARTICLE", 
                                   command=lambda url=article["url"]: webbrowser.open(url),
                                   bg=article["color"], fg="#000", font=("Helvetica", 10, "bold"), 
                                   padx=18, pady=7, relief=tk.FLAT, cursor="hand2", 
                                   activebackground="#00ff88", activeforeground="#000")
            link_button.pack(anchor="w")

def main():
    """Main entry point"""
    root = tk.Tk()
    app = NewsAnalyzerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
