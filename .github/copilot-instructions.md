# News Analyzer & Fake News Detector - Setup Instructions

This is a **Streamlit-based News Analyzer & Fake News Detector** application with AI-powered summaries, credibility scoring, and sentiment analysis.

## Quick Setup

### Step 1: Get API Keys
- **NewsAPI**: https://newsapi.org/register
- **Gemini API**: https://aistudio.google.com/apikey

### Step 2: Configure Environment
Create a `.env` file in the root directory:
```
NEWSAPI_KEY=your_newsapi_key_here
GEMINI_KEY=your_gemini_key_here
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the App
```bash
streamlit run news_analyzer.py
```

## Project Structure

```
news-analyzer/
├── news_analyzer.py          # Main Streamlit app
├── requirements.txt          # Python dependencies
├── .env.example             # API key template
├── .env                     # Your actual keys (git ignored)
├── README.md                # Full documentation
├── QUICK_START.txt          # 5-minute setup
├── CODE_EXPLANATION.txt     # How it works (beginner-friendly)
├── ARCHITECTURE.txt         # System design
├── PRESENTATION_SCRIPT.txt  # What to say
└── PRESENTATION_CHECKLIST.txt # Before presentation
```

## Features

✅ **Real-time News Fetching** - Connects to NewsAPI for current articles
✅ **Credibility Scoring** - Rates source trustworthiness (0-100%)
✅ **AI Summaries** - Uses Google Gemini to summarize articles
✅ **Sentiment Analysis** - Detects positive/negative/neutral tone
✅ **Smart Sorting** - Sort by credibility, date, or sentiment
✅ **Beautiful UI** - Full-featured Streamlit interface

## Key Components

1. **NewsAPI Integration** - Fetches 10 articles per search
2. **Gemini AI** - Generates 1-2 sentence AI summaries
3. **TextBlob** - Performs sentiment analysis
4. **Custom Credibility Engine** - Source reputation + language analysis
5. **Streamlit Frontend** - Beautiful, responsive web interface

## Troubleshooting

**API Key Not Found**: Ensure `.env` file is in the same folder as `news_analyzer.py`

**Network Error**: Check your internet connection; APIs require network access

**Slow Performance**: Disable "Generate AI Summaries" for faster results

**Import Errors**: Run `pip install -r requirements.txt` again

## Presentation Tips

- Demo with trending topics (Tesla, AI, Bitcoin, etc.)
- Highlight credibility score differences between BBC (95%) and unknown blogs (40%)
- Show AI summaries working in real-time
- Sort by sentiment to show emotional tone analysis
- Always have screenshots ready as backup

See PRESENTATION_SCRIPT.txt for full talking points.
