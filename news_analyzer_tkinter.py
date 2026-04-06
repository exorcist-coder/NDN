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
        self.root.configure(bg="#1e1e1e")
        
        self.articles = []
        self.current_sort = "credibility"
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup futuristic AI-powered 2026 news interface"""
        
        # ===== HEADER SECTION =====
        header_frame = tk.Frame(self.root, bg="#242424", height=110)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Top accent
        accent_top = tk.Frame(header_frame, bg="#5b8fc4", height=2)
        accent_top.pack(fill=tk.X)
        
        # Title section
        title_section = tk.Frame(header_frame, bg="#242424")
        title_section.pack(fill=tk.X, padx=40, pady=(12, 0))
        
        title_label = tk.Label(title_section, text="◆ NEWS ANALYZER AI ◆", 
                              font=("Helvetica", 26, "bold"), bg="#242424", fg="#5b8fc4")
        title_label.pack(pady=(0, 2))
        
        subtitle = tk.Label(header_frame, text="next-generation credibility intelligence | real-time analysis engine | fact-verified reporting", 
                           font=("Helvetica", 8), bg="#242424", fg="#6ec46d")
        subtitle.pack(pady=(0, 8))
        
        # ===== SEARCH SECTION =====
        search_frame = tk.Frame(self.root, bg="#1e1e1e", height=95)
        search_frame.pack(fill=tk.X, padx=0, pady=0)
        search_frame.pack_propagate(False)
        
        search_inner = tk.Frame(search_frame, bg="#1e1e1e")
        search_inner.pack(fill=tk.X, padx=40, pady=15)
        
        tk.Label(search_inner, text="🔍 SEARCH:", font=("Helvetica", 11, "bold"), 
                bg="#1e1e1e", fg="#5b8fc4").pack(side=tk.LEFT, padx=(0, 15))
        
        self.search_entry = tk.Entry(search_inner, font=("Helvetica", 12), width=42, relief=tk.FLAT, 
                                     bg="#2d2d2d", fg="#6ec46d", bd=0, highlightthickness=2, 
                                     highlightbackground="#5b8fc4", highlightcolor="#5b8fc4", insertbackground="#5b8fc4")
        self.search_entry.pack(side=tk.LEFT, padx=(0, 15), ipady=9)
        self.search_entry.insert(0, "Technology")
        
        search_btn = tk.Button(search_inner, text="❯ ANALYZE", command=self.search_news, 
                              bg="#5b8fc4", fg="#1e1e1e", font=("Helvetica", 11, "bold"), 
                              padx=25, pady=8, relief=tk.FLAT, cursor="hand2", 
                              activebackground="#6ec46d", activeforeground="#1e1e1e")
        search_btn.pack(side=tk.LEFT)
        
        # ===== CONTROLS SECTION =====
        controls_frame = tk.Frame(self.root, bg="#1e1e1e", height=65)
        controls_frame.pack(fill=tk.X, padx=0, pady=0)
        controls_frame.pack_propagate(False)
        
        controls_inner = tk.Frame(controls_frame, bg="#1e1e1e")
        controls_inner.pack(fill=tk.X, padx=40, pady=12)
        
        tk.Label(controls_inner, text="SORT:", font=("Helvetica", 10, "bold"), 
                bg="#1e1e1e", fg="#5b8fc4").pack(side=tk.LEFT, padx=(0, 20))
        
        self.sort_var = tk.StringVar(value="credibility")
        sort_items = [("⚡ CREDIBILITY", "credibility"), ("⏰ LATEST", "date"), ("💭 SENTIMENT", "sentiment")]
        
        for text, value in sort_items:
            rb = tk.Radiobutton(controls_inner, text=text, variable=self.sort_var, value=value, 
                               command=lambda v=value: self.sort_articles(v), bg="#1e1e1e", 
                               font=("Helvetica", 10, "bold"), fg="#6ec46d", activebackground="#1e1e1e",
                               activeforeground="#5b8fc4", selectcolor="#1e1e1e")
            rb.pack(side=tk.LEFT, padx=(0, 25))
        
        # ===== ARTICLES CONTAINER =====
        articles_frame = tk.Frame(self.root, bg="#1e1e1e")
        articles_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        canvas = tk.Canvas(articles_frame, bg="#1e1e1e", highlightthickness=0, bd=0)
        
        scrollbar_style = ttk.Style()
        scrollbar_style.theme_use('clam')
        scrollbar_style.configure('Vertical.TScrollbar', background="#2d2d2d", troughcolor="#1e1e1e")
        
        scrollbar = ttk.Scrollbar(articles_frame, orient="vertical", command=canvas.yview, style='Vertical.TScrollbar')
        scrollable_frame = tk.Frame(canvas, bg="#1e1e1e")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y", padx=(0, 5))
        
        self.articles_container = scrollable_frame
        
        # ===== STATUS BAR =====
        status_frame = tk.Frame(self.root, bg="#242424", height=45)
        status_frame.pack(fill=tk.X, padx=0, pady=0)
        status_frame.pack_propagate(False)
        
        bottom_accent = tk.Frame(status_frame, bg="#5b8fc4", height=2)
        bottom_accent.pack(fill=tk.X)
        
        self.status_label = tk.Label(status_frame, text="▸ Ready. Enter a search query to analyze articles.", 
                                     bg="#242424", fg="#6ec46d", font=("Helvetica", 9, "bold"), anchor="w", padx=40, pady=10)
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
        """Display articles with next-gen 2026 futuristic design"""
        # Clear previous articles
        for widget in self.articles_container.winfo_children():
            widget.destroy()
        
        if not self.articles:
            no_results = tk.Label(self.articles_container, text="◆ NO ARTICLES FOUND ◆", 
                                 font=("Helvetica", 16, "bold"), bg="#1e1e1e", fg="#5b8fc4")
            no_results.pack(pady=120)
            return
        
        # Main container
        main_container = tk.Frame(self.articles_container, bg="#1e1e1e")
        main_container.pack(fill=tk.BOTH, expand=True, padx=35, pady=25)
        
        # Article stats banner
        stats_frame = tk.Frame(main_container, bg="#242424")
        stats_frame.pack(fill=tk.X, pady=(0, 20))
        stats_frame.pack_propagate(False)
        stats_frame.configure(height=50)
        
        avg_cred = sum(a["credibility"] for a in self.articles) / len(self.articles)
        stats_text = f"◆ {len(self.articles)} ARTICLES  •  AVG CREDIBILITY: {avg_cred:.0f}%  •  SORTED BY: {self.sort_var.get().upper()} ◆"
        stats_label = tk.Label(stats_frame, text=stats_text, font=("Helvetica", 8, "bold"), 
                              fg="#6ec46d", bg="#242424")
        stats_label.pack(pady=8)
        
        for idx, article in enumerate(self.articles, 1):
            # Outer wrapper
            card_wrapper = tk.Frame(main_container, bg="#1e1e1e")
            card_wrapper.pack(fill=tk.X, pady=(0, 22))
            
            # Top accent bar
            cred = article["credibility"]
            color = article["color"]
            top_bar = tk.Frame(card_wrapper, bg=color, height=5)
            top_bar.pack(fill=tk.X)
            top_bar.pack_propagate(False)
            
            # Main card
            card = tk.Frame(card_wrapper, bg="#2d2d2d", relief=tk.FLAT, bd=0)
            card.pack(fill=tk.BOTH, expand=True)
            
            # Inner content
            inner = tk.Frame(card, bg="#242424", padx=24, pady=20)
            inner.pack(fill=tk.BOTH, expand=True)
            
            # ===== ROW 1: INDEX + SOURCE + CONTROLS =====
            row1 = tk.Frame(inner, bg="#242424")
            row1.pack(fill=tk.X, pady=(0, 10))
            
            # Left: Number and source
            left1 = tk.Frame(row1, bg="#242424")
            left1.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            index_src = tk.Label(left1, text=f"#{idx:02d}  •  {article['source'].upper()}", 
                                font=("Helvetica", 9, "bold"), fg="#6ec46d", bg="#242424")
            index_src.pack(anchor="w")
            
            # Right: Credibility visual + percentage
            right1 = tk.Frame(row1, bg="#242424")
            right1.pack(side=tk.RIGHT)
            
            cred_viz = tk.Frame(right1, bg="#242424")
            cred_viz.pack()
            
            cred_bar_bg = tk.Frame(cred_viz, bg="#2d2d2d", width=120, height=8)
            cred_bar_bg.pack()
            cred_bar_bg.pack_propagate(False)
            
            cred_bar_fill = tk.Frame(cred_bar_bg, bg=color, height=8, width=int(120 * cred / 100))
            cred_bar_fill.pack(side=tk.LEFT)
            cred_bar_fill.pack_propagate(False)
            
            cred_pct = tk.Label(cred_viz, text=f"{cred}% CREDIBLE", 
                               font=("Helvetica", 9, "bold"), fg=color, bg="#242424")
            cred_pct.pack(pady=(2, 0))
            
            # ===== ROW 2: TITLE =====
            title = tk.Label(inner, text=article['title'], 
                           font=("Helvetica", 13, "bold"), fg="#e1e8ed", bg="#242424",
                           wraplength=1050, justify=tk.LEFT)
            title.pack(anchor="w", pady=(0, 12))
            
            # ===== ROW 3: METADATA =====
            row3 = tk.Frame(inner, bg="#242424")
            row3.pack(fill=tk.X, pady=(0, 12))
            
            date_tag = tk.Label(row3, text=f"📅 {article['published']}", 
                               font=("Helvetica", 8), fg="#5b8fc4", bg="#242424")
            date_tag.pack(side=tk.LEFT, padx=(0, 16))
            
            mood_tag = tk.Label(row3, text=f"💭 {article['sentiment']}", 
                               font=("Helvetica", 8), fg="#8b7aa8", bg="#242424")
            mood_tag.pack(side=tk.LEFT)
            
            # ===== ROW 4: SUMMARY =====
            summary = tk.Label(inner, text=article["summary"], 
                             font=("Helvetica", 10), fg="#a0a8b0", bg="#242424",
                             wraplength=1050, justify=tk.LEFT)
            summary.pack(fill=tk.X, pady=(0, 16))
            
            # ===== ROW 5: ACTION BUTTONS =====
            buttons = tk.Frame(inner, bg="#242424")
            buttons.pack(fill=tk.X)
            
            read_btn = tk.Button(buttons, text="► READ", 
                                command=lambda url=article["url"]: webbrowser.open(url),
                                bg=color, fg="#1e1e1e", font=("Helvetica", 9, "bold"), 
                                padx=16, pady=6, relief=tk.FLAT, cursor="hand2",
                                activebackground="#6ec46d", activeforeground="#1e1e1e")
            read_btn.pack(side=tk.LEFT, padx=(0, 8))
            
            share_btn = tk.Button(buttons, text="⬈", 
                                 bg="#2d2d2d", fg="#5b8fc4", font=("Helvetica", 10, "bold"),
                                 padx=10, pady=5, relief=tk.FLAT, cursor="hand2",
                                 activebackground="#5b8fc4", activeforeground="#1e1e1e")
            share_btn.pack(side=tk.LEFT)

def main():
    """Main entry point"""
    root = tk.Tk()
    app = NewsAnalyzerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
