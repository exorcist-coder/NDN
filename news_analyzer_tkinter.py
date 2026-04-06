import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import requests
from datetime import datetime, timedelta
import google.generativeai as genai
from textblob import TextBlob
import os
from dotenv import load_dotenv
import webbrowser

# Load environment variables
load_dotenv()

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
    "twitter": 35, "reddit": 30, "unknown": 65
}

def get_credibility_score(source, content):
    """Calculate credibility score based on source and content"""
    source_lower = source.lower()
    base_score = CREDIBILITY_SCORES.get("unknown", 65)
    
    for known_source, score in CREDIBILITY_SCORES.items():
        if known_source in source_lower:
            base_score = score
            break
    
    exclamation_count = content.count("!")
    caps_words = len([w for w in content.split() if w.isupper() and len(w) > 1])
    
    if exclamation_count > 5:
        base_score -= 5
    if caps_words > 10:
        base_score -= 3
    
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
        return None, "❌ NewsAPI key not found! Please set NEWSAPI_KEY environment variable."
    
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
            return data["articles"], None
        else:
            return None, f"API Error: {data.get('message', 'Unknown error')}"
    except requests.exceptions.RequestException as e:
        return None, f"❌ Network error: {str(e)}"

class NewsAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📰 News Analyzer & Fake News Detector")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")
        
        self.articles = []
        self.current_sort = "date"
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        
        # Header
        header_frame = tk.Frame(self.root, bg="#1f77b4", height=60)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        
        title_label = tk.Label(header_frame, text="📰 News Analyzer & Fake News Detector", 
                              font=("Arial", 20, "bold"), bg="#1f77b4", fg="white")
        title_label.pack(pady=10)
        
        # Search Frame
        search_frame = tk.Frame(self.root, bg="#f0f0f0")
        search_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(search_frame, text="Search:", font=("Arial", 10), bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        
        self.search_entry = tk.Entry(search_frame, font=("Arial", 10), width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.insert(0, "AI")
        
        tk.Button(search_frame, text="Search", command=self.search_news, 
                 bg="#28a745", fg="white", font=("Arial", 10), padx=20).pack(side=tk.LEFT, padx=5)
        
        # Options frame
        options_frame = tk.Frame(self.root, bg="#f0f0f0")
        options_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(options_frame, text="Sort by:", font=("Arial", 9), bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        
        sort_var = tk.StringVar(value="date")
        tk.Radiobutton(options_frame, text="Date", variable=sort_var, value="date", 
                      command=lambda: self.sort_articles("date"), bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(options_frame, text="Credibility", variable=sort_var, value="credibility",
                      command=lambda: self.sort_articles("credibility"), bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(options_frame, text="Sentiment", variable=sort_var, value="sentiment",
                      command=lambda: self.sort_articles("sentiment"), bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        
        self.summarize_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="AI Summaries", variable=self.summarize_var, 
                      bg="#f0f0f0").pack(side=tk.LEFT, padx=20)
        
        # Articles frame (scrollable)
        articles_frame = tk.Frame(self.root, bg="#f0f0f0")
        articles_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Canvas with scrollbar
        canvas = tk.Canvas(articles_frame, bg="#f0f0f0", highlightthickness=0)
        scrollbar = ttk.Scrollbar(articles_frame, orient="vertical", command=canvas.scroll)
        scrollable_frame = tk.Frame(canvas, bg="#f0f0f0")
        
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
        self.status_label = tk.Label(self.root, text="Ready", bg="#e0e0e0", font=("Arial", 9), anchor="w")
        self.status_label.pack(fill=tk.X, padx=0, pady=0)
    
    def search_news(self):
        """Search for news articles"""
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("Warning", "Please enter a search term")
            return
        
        self.status_label.config(text="Searching...")
        self.root.update()
        
        # Run in thread to avoid freezing UI
        thread = threading.Thread(target=self._perform_search, args=(query,))
        thread.daemon = True
        thread.start()
    
    def _perform_search(self, query):
        """Perform search in background thread"""
        articles, error = fetch_news(query)
        
        if error:
            self.root.after(0, lambda: messagebox.showerror("Error", error))
            self.status_label.config(text="Error fetching news")
            return
        
        if not articles:
            self.root.after(0, lambda: messagebox.showinfo("Info", "No articles found"))
            self.status_label.config(text="No articles found")
            return
        
        self.articles = []
        for idx, article in enumerate(articles):
            title = article.get("title", "N/A")
            source = article.get("source", {}).get("name", "Unknown")
            content = article.get("description", "") + " " + article.get("content", "")
            url = article.get("url", "")
            published = article.get("publishedAt", "N/A")[:10]
            
            credibility = get_credibility_score(source, content)
            sentiment, polarity = get_sentiment(content)
            
            summary = ""
            if self.summarize_var.get() and GEMINI_KEY:
                summary = summarize_with_gemini(content, title)
            else:
                summary = article.get("description", "No summary available")[:150]
            
            self.articles.append({
                "title": title,
                "source": source,
                "credibility": credibility,
                "sentiment": sentiment,
                "summary": summary,
                "url": url,
                "published": published
            })
        
        self.root.after(0, self.display_articles)
        self.root.after(0, lambda: self.status_label.config(text=f"Found {len(self.articles)} articles"))
    
    def sort_articles(self, sort_by):
        """Sort articles"""
        if sort_by == "credibility":
            self.articles.sort(key=lambda x: x["credibility"], reverse=True)
        elif sort_by == "sentiment":
            self.articles.sort(key=lambda x: x["sentiment"], reverse=True)
        else:  # date
            self.articles.sort(key=lambda x: x["published"], reverse=True)
        
        self.display_articles()
    
    def display_articles(self):
        """Display articles in UI"""
        # Clear previous articles
        for widget in self.articles_container.winfo_children():
            widget.destroy()
        
        for idx, article in enumerate(self.articles, 1):
            card_frame = tk.Frame(self.articles_container, bg="white", relief=tk.RAISED)
            card_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Title and source
            title_frame = tk.Frame(card_frame, bg="white")
            title_frame.pack(fill=tk.X, padx=10, pady=5)
            
            title_label = tk.Label(title_frame, text=f"{idx}. {article['title'][:100]}", 
                                  font=("Arial", 11, "bold"), bg="white", wraplength=800, justify=tk.LEFT)
            title_label.pack(anchor="w")
            
            source_label = tk.Label(title_frame, text=f"Source: {article['source']} | {article['published']}", 
                                   font=("Arial", 8), fg="#666", bg="white")
            source_label.pack(anchor="w")
            
            # Credibility and sentiment
            info_frame = tk.Frame(card_frame, bg="white")
            info_frame.pack(fill=tk.X, padx=10, pady=3)
            
            # Credibility color
            cred_color = "#28a745" if article["credibility"] >= 80 else ("#ffc107" if article["credibility"] >= 50 else "#dc3545")
            cred_label = tk.Label(info_frame, text=f"Credibility: {article['credibility']}%", 
                                 font=("Arial", 9, "bold"), fg=cred_color, bg="white")
            cred_label.pack(side=tk.LEFT, padx=5)
            
            sentiment_label = tk.Label(info_frame, text=article["sentiment"], 
                                      font=("Arial", 9), bg="white")
            sentiment_label.pack(side=tk.LEFT, padx=5)
            
            # Summary
            summary_label = tk.Label(card_frame, text=article["summary"][:200], 
                                    font=("Arial", 9), bg="white", wraplength=800, justify=tk.LEFT)
            summary_label.pack(fill=tk.X, padx=10, pady=5)
            
            # Open link button
            link_button = tk.Button(card_frame, text="Read Full Article", 
                                   command=lambda url=article["url"]: webbrowser.open(url),
                                   bg="#1f77b4", fg="white", font=("Arial", 8), padx=10)
            link_button.pack(anchor="e", padx=10, pady=5)

def main():
    """Main entry point"""
    root = tk.Tk()
    app = NewsAnalyzerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
