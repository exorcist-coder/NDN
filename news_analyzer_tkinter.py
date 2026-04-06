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
from PIL import Image, ImageTk
from io import BytesIO

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

def clean_summary(text, max_length=200):
    """Clean and validate summary text"""
    if not text or not isinstance(text, str):
        return "No summary available"
    
    # Remove URLs and file paths
    cleaned = text
    import re
    cleaned = re.sub(r'https?://\S+', '', cleaned)
    cleaned = re.sub(r'\S+\.\w+/\S+', '', cleaned)  # Remove file paths
    cleaned = re.sub(r'\[.*?\]', '', cleaned)  # Remove brackets
    
    # Clean up whitespace
    cleaned = ' '.join(cleaned.split())
    
    # Truncate at sentence boundary
    if len(cleaned) > max_length:
        truncated = cleaned[:max_length]
        last_period = truncated.rfind('.')
        last_comma = truncated.rfind(',')
        last_space = truncated.rfind(' ')
        
        cut_pos = max(last_period, last_comma, last_space)
        if cut_pos > max_length - 50:
            cleaned = truncated[:cut_pos+1]
        else:
            cleaned = truncated.rstrip() + "..."
    
    return cleaned.strip() if cleaned.strip() else "No summary available"

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
        self.root.title("📰 News Analyzer & Credibility Detector")
        self.root.geometry("1400x850")
        self.root.configure(bg="#f5f5f5")
        
        self.articles = []
        self.current_sort = "credibility"
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the professional user interface"""
        
        # Header
        header_frame = tk.Frame(self.root, bg="#1a1a1a", height=70)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        
        title_label = tk.Label(header_frame, text="📰 NEWS ANALYZER", 
                              font=("Segoe UI", 22, "bold"), bg="#1a1a1a", fg="#00d4ff")
        title_label.pack(pady=10)
        
        subtitle = tk.Label(header_frame, text="Real-time Credibility Scoring | Sentiment Analysis | Fact-Based Journalism", 
                           font=("Segoe UI", 9), bg="#1a1a1a", fg="#888")
        subtitle.pack()
        
        # Search Frame
        search_frame = tk.Frame(self.root, bg="#f5f5f5")
        search_frame.pack(fill=tk.X, padx=20, pady=15)
        
        tk.Label(search_frame, text="Search Topic:", font=("Segoe UI", 11, "bold"), bg="#f5f5f5").pack(side=tk.LEFT, padx=5)
        
        self.search_entry = tk.Entry(search_frame, font=("Segoe UI", 11), width=35, relief=tk.FLAT)
        self.search_entry.pack(side=tk.LEFT, padx=10)
        self.search_entry.insert(0, "Technology")
        
        tk.Button(search_frame, text="🔍 SEARCH", command=self.search_news, 
                 bg="#00d4ff", fg="#000", font=("Segoe UI", 10, "bold"), padx=25, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        # Options frame
        options_frame = tk.Frame(self.root, bg="#f5f5f5")
        options_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(options_frame, text="Sort By:", font=("Segoe UI", 10, "bold"), bg="#f5f5f5").pack(side=tk.LEFT, padx=5)
        
        self.sort_var = tk.StringVar(value="credibility")
        tk.Radiobutton(options_frame, text="Credibility ▼", variable=self.sort_var, value="credibility", 
                      command=lambda: self.sort_articles("credibility"), bg="#f5f5f5", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(options_frame, text="Latest", variable=self.sort_var, value="date",
                      command=lambda: self.sort_articles("date"), bg="#f5f5f5", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(options_frame, text="Sentiment", variable=self.sort_var, value="sentiment",
                      command=lambda: self.sort_articles("sentiment"), bg="#f5f5f5", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=10)
        
        # Articles frame (scrollable)
        articles_frame = tk.Frame(self.root, bg="#f5f5f5")
        articles_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Canvas with scrollbar
        canvas = tk.Canvas(articles_frame, bg="#f5f5f5", highlightthickness=0)
        scrollbar = ttk.Scrollbar(articles_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f5f5f5")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.articles_container = scrollable_frame
        
        # Status bar
        self.status_label = tk.Label(self.root, text="Ready. Enter a search term to begin.", 
                                     bg="#2a2a2a", fg="#00d4ff", font=("Segoe UI", 9), anchor="w", padx=10)
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
            image = article.get("urlToImage", "")
            
            credibility, color = get_credibility_score(source, full_content)
            sentiment = get_sentiment(full_content)
            
            summary = clean_summary(description, max_length=180)
            
            self.articles.append({
                "title": title,
                "source": source,
                "credibility": credibility,
                "color": color,
                "sentiment": sentiment,
                "summary": summary,
                "url": url,
                "image": image,
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
    
    def load_image_async(self, card_frame, url, width=250, height=150):
        """Load image from URL asynchronously"""
        def fetch_and_display():
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    img_data = Image.open(BytesIO(response.content))
                    img_data.thumbnail((width, height), Image.Resampling.LANCZOS)
                    
                    # Convert to PhotoImage
                    photo = ImageTk.PhotoImage(img_data)
                    
                    # Create image label
                    img_label = tk.Label(card_frame, image=photo, bg="white")
                    img_label.image = photo  # Keep a reference
                    img_label.pack(fill=tk.X, padx=0, pady=0)
            except:
                pass  # Silently fail if image can't be loaded
        
        threading.Thread(target=fetch_and_display, daemon=True).start()

    def display_articles(self):
        """Display articles with professional styling and thumbnails"""
        for widget in self.articles_container.winfo_children():
            widget.destroy()
        
        if not self.articles:
            no_results = tk.Label(self.articles_container, text="No articles to display", 
                                 font=("Segoe UI", 12), bg="#f5f5f5", fg="#999")
            no_results.pack(pady=40)
            return
        
        for idx, article in enumerate(self.articles, 1):
            card_frame = tk.Frame(self.articles_container, bg="white", relief=tk.FLAT, bd=1)
            card_frame.pack(fill=tk.X, padx=5, pady=8)
            
            # Left accent bar (color coded by credibility score)
            accent_color = article["color"]
            cred = article["credibility"]
            
            accent_frame = tk.Frame(card_frame, bg=accent_color, width=4)
            accent_frame.pack(side=tk.LEFT, fill=tk.Y)
            
            content_frame = tk.Frame(card_frame, bg="white")
            content_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
            
            # Load and display thumbnail asynchronously if available
            image_url = article.get("image") or article.get("urlToImage")
            if image_url:
                self.load_image_async(content_frame, image_url, width=600, height=180)
            
            # Text content frame
            text_frame = tk.Frame(content_frame, bg="white")
            text_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)
            
            # Title
            title_label = tk.Label(text_frame, text=f"{idx}. {article['title']}", 
                                  font=("Segoe UI", 12, "bold"), bg="white", wraplength=1200, justify=tk.LEFT)
            title_label.pack(anchor="w", pady=(0, 8))
            
            # Source and date row
            meta_frame = tk.Frame(text_frame, bg="white")
            meta_frame.pack(fill=tk.X, pady=(0, 8))
            
            source_label = tk.Label(meta_frame, text=f"📰 {article['source']}", 
                                   font=("Segoe UI", 9), fg="#555", bg="white")
            source_label.pack(side=tk.LEFT, padx=(0, 15))
            
            date_label = tk.Label(meta_frame, text=f"📅 {article['published']}", 
                                 font=("Segoe UI", 9), fg="#555", bg="white")
            date_label.pack(side=tk.LEFT, padx=(0, 15))
            
            sentiment_label = tk.Label(meta_frame, text=article["sentiment"], 
                                      font=("Segoe UI", 9), bg="white")
            sentiment_label.pack(side=tk.LEFT)
            
            # Credibility score (prominent)
            cred_text = f"CREDIBILITY: {cred}%"
            cred_label = tk.Label(meta_frame, text=cred_text, 
                                 font=("Segoe UI", 10, "bold"), fg=accent_color, bg="white")
            cred_label.pack(side=tk.RIGHT, padx=(10, 0))
            
            # Summary
            summary_label = tk.Label(text_frame, text=article["summary"], 
                                    font=("Segoe UI", 9), bg="white", wraplength=1200, justify=tk.LEFT, fg="#333")
            summary_label.pack(fill=tk.X, pady=(0, 8))
            
            # Read button
            link_button = tk.Button(text_frame, text="→ Read Full Article", 
                                   command=lambda url=article["url"]: webbrowser.open(url),
                                   bg=accent_color, fg="white", font=("Segoe UI", 9, "bold"), 
                                   padx=15, pady=5, relief=tk.FLAT, cursor="hand2")
            link_button.pack(anchor="w")

def main():
    """Main entry point"""
    root = tk.Tk()
    app = NewsAnalyzerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
