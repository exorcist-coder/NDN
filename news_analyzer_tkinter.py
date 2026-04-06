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
        self.root.title("The News Analyzer - Credibility Scoring & Fact-Based Journalism")
        self.root.geometry("1200x900")
        self.root.configure(bg="white")
        
        self.articles = []
        self.current_sort = "credibility"
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the professional user interface - NYT style"""
        
        # Header - Clean and minimal like NYT
        header_frame = tk.Frame(self.root, bg="white", height=80)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="THE NEWS ANALYZER", 
                              font=("Georgia", 28, "bold"), bg="white", fg="#000")
        title_label.pack(pady=(15, 3))
        
        divider = tk.Frame(header_frame, bg="#000", height=2)
        divider.pack(fill=tk.X, padx=50)
        
        subtitle = tk.Label(header_frame, text="Independent Analysis • Credibility Scoring • Real-Time Journalism", 
                           font=("Georgia", 9), bg="white", fg="#666")
        subtitle.pack(pady=(5, 0))
        
        # Search Frame - Elegant
        search_frame = tk.Frame(self.root, bg="white", height=70)
        search_frame.pack(fill=tk.X, padx=0, pady=0)
        search_frame.pack_propagate(False)
        
        inner_search = tk.Frame(search_frame, bg="white")
        inner_search.pack(fill=tk.X, padx=50, pady=15)
        
        tk.Label(inner_search, text="Search:", font=("Georgia", 11, "bold"), bg="white", fg="#000").pack(side=tk.LEFT, padx=(0, 10))
        
        self.search_entry = tk.Entry(inner_search, font=("Georgia", 12), width=40, relief=tk.FLAT, bg="#f5f5f5", 
                                     bd=0, highlightthickness=1, highlightbackground="#ddd", highlightcolor="#999")
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10), ipady=6)
        self.search_entry.insert(0, "Technology")
        
        tk.Button(inner_search, text="SEARCH", command=self.search_news, 
                 bg="#000", fg="white", font=("Georgia", 11, "bold"), padx=20, pady=5, relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT)
        
        # Options frame - Subtle
        options_frame = tk.Frame(self.root, bg="white", height=50)
        options_frame.pack(fill=tk.X, padx=0, pady=0)
        options_frame.pack_propagate(False)
        
        inner_options = tk.Frame(options_frame, bg="white")
        inner_options.pack(fill=tk.X, padx=50, pady=10)
        
        tk.Label(inner_options, text="Sort by:", font=("Georgia", 10), bg="white", fg="#333").pack(side=tk.LEFT, padx=(0, 20))
        
        self.sort_var = tk.StringVar(value="credibility")
        for text, value in [("Credibility", "credibility"), ("Latest", "date"), ("Sentiment", "sentiment")]:
            tk.Radiobutton(inner_options, text=text, variable=self.sort_var, value=value, 
                          command=lambda v=value: self.sort_articles(v), bg="white", font=("Georgia", 10), 
                          fg="#333", activebackground="white").pack(side=tk.LEFT, padx=(0, 25))
        
        # Articles frame (scrollable) - Magazine-style
        articles_frame = tk.Frame(self.root, bg="white")
        articles_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Canvas with scrollbar
        canvas = tk.Canvas(articles_frame, bg="white", highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(articles_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.articles_container = scrollable_frame
        
        # Status bar - Minimal
        self.status_label = tk.Label(self.root, text="Ready. Enter a search term to begin.", 
                                     bg="white", fg="#666", font=("Georgia", 9), anchor="w", padx=50, pady=8)
        self.status_label.pack(fill=tk.X, padx=0, pady=0)
    
    def search_news(self):
        """Search for news articles"""
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("Input Required", "Please enter a search term")
            return
        
        self.status_label.config(text="🔄 Searching for articles...")
        self.root.update()
        
        thread = threading.Thread(target=self._perform_search, args=(query,))
        thread.daemon = True
        thread.start()
    
    def _perform_search(self, query):
        """Perform search in background thread"""
        articles, error = fetch_news(query)
        
        if error:
            self.root.after(0, lambda: messagebox.showerror("Error", error))
            self.status_label.config(text="⚠️ Error fetching news")
            return
        
        if not articles:
            self.root.after(0, lambda: messagebox.showinfo("No Results", "No articles found for this topic"))
            self.status_label.config(text="No articles found")
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
        self.root.after(0, lambda: self.status_label.config(text=f"✓ Found {len(self.articles)} articles. Sorted by credibility."))
    
    def sort_articles(self, sort_by):
        """Sort articles"""
        if sort_by == "credibility":
            self.articles.sort(key=lambda x: x["credibility"], reverse=True)
        elif sort_by == "sentiment":
            self.articles.sort(key=lambda x: x["sentiment"])
        else:  # date
            self.articles.sort(key=lambda x: x["published"], reverse=True)
        
        self.display_articles()
        self.status_label.config(text=f"✓ Sorted by {sort_by.capitalize()}")
    
    def display_articles(self):
        """Display articles with New York Times-style design"""
        # Clear previous articles
        for widget in self.articles_container.winfo_children():
            widget.destroy()
        
        if not self.articles:
            no_results = tk.Label(self.articles_container, text="No articles to display", 
                                 font=("Georgia", 14), bg="white", fg="#999")
            no_results.pack(pady=80)
            return
        
        # Main articles container with padding
        main_container = tk.Frame(self.articles_container, bg="white")
        main_container.pack(fill=tk.BOTH, expand=True, padx=50, pady=30)
        
        for idx, article in enumerate(self.articles, 1):
            # Article card
            card_frame = tk.Frame(main_container, bg="white", relief=tk.FLAT)
            card_frame.pack(fill=tk.X, pady=(0, 40))
            
            # Left accent bar based on credibility
            accent_color = article["color"]
            accent_frame = tk.Frame(card_frame, bg=accent_color, width=3)
            accent_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
            
            # Main content area
            content_frame = tk.Frame(card_frame, bg="white")
            content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Credibility badge at top right
            badge_frame = tk.Frame(content_frame, bg="white")
            badge_frame.pack(fill=tk.X, pady=(0, 8))
            
            cred = article["credibility"]
            cred_badge = tk.Label(badge_frame, text=f"{cred}% CREDIBLE", 
                                 font=("Georgia", 9, "bold"), bg="white", fg=accent_color)
            cred_badge.pack(anchor="e")
            
            # Title - Large and prominent (NYT style)
            title_label = tk.Label(content_frame, text=article['title'], 
                                  font=("Georgia", 16, "bold"), bg="white", fg="#000",
                                  wraplength=900, justify=tk.LEFT)
            title_label.pack(anchor="w", pady=(0, 10))
            
            # Meta information (source, date, sentiment)
            meta_frame = tk.Frame(content_frame, bg="white")
            meta_frame.pack(fill=tk.X, pady=(0, 12))
            
            source_label = tk.Label(meta_frame, text=article['source'].upper(), 
                                   font=("Georgia", 9, "bold"), fg="#333", bg="white")
            source_label.pack(side=tk.LEFT, padx=(0, 15))
            
            date_label = tk.Label(meta_frame, text=article['published'], 
                                 font=("Georgia", 9), fg="#666", bg="white")
            date_label.pack(side=tk.LEFT, padx=(0, 15))
            
            sentiment_label = tk.Label(meta_frame, text=article["sentiment"], 
                                      font=("Georgia", 9), bg="white")
            sentiment_label.pack(side=tk.LEFT)
            
            # Summary - Article excerpt style
            summary_label = tk.Label(content_frame, text=article["summary"], 
                                    font=("Georgia", 11), bg="white", fg="#333",
                                    wraplength=900, justify=tk.LEFT, pady=3)
            summary_label.pack(fill=tk.X, pady=(0, 12))
            
            # Read button - Subtle
            link_button = tk.Button(content_frame, text="READ FULL ARTICLE →", 
                                   command=lambda url=article["url"]: webbrowser.open(url),
                                   bg=accent_color, fg="white", font=("Georgia", 9, "bold"), 
                                   padx=15, pady=6, relief=tk.FLAT, cursor="hand2", 
                                   activebackground="#000", activeforeground="white")
            link_button.pack(anchor="w")
            
            # Divider line between articles
            if idx < len(self.articles):
                divider = tk.Frame(main_container, bg="#e0e0e0", height=1)
                divider.pack(fill=tk.X, pady=(30, 0))

def main():
    """Main entry point"""
    root = tk.Tk()
    app = NewsAnalyzerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
