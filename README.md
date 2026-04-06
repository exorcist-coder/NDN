# 📰 Automated News Summarizer & Fake News Detector

## 🚀 START HERE

You have **4 hours to get running and present tomorrow**. Here's exactly what to do:

---

## 📋 FILES YOU HAVE

| File | Purpose | Read Time |
|------|---------|-----------|
| **news_analyzer.py** | The actual working app | Don't read - just run it |
| **requirements.txt** | Dependencies to install | Install, don't read |
| **.env.example** | API key template | Copy to create .env |
| **QUICK_START.txt** | 5-minute setup guide | ⭐ READ THIS FIRST |
| **CODE_EXPLANATION.txt** | Grade 7 level explanation | 20 min (optional but helps) |
| **ARCHITECTURE.txt** | How everything connects | 15 min (visual diagrams) |
| **PRESENTATION_SCRIPT.txt** | What to say tomorrow | 10 min (memorize key parts) |
| **PRESENTATION_CHECKLIST.txt** | Pre-presentation checklist | 5 min (read before bed) |

---

## ⏱️ YOUR TIMELINE

### **Tonight (Next 2 Hours)**

**5 minutes:** Get API keys
- NewsAPI: https://newsapi.org/register (copy your key)
- Gemini: https://aistudio.google.com/apikey (copy your key)

**5 minutes:** Setup
- Create folder called `news-analyzer`
- Put 3 files in it:
  - `news_analyzer.py`
  - `requirements.txt`
  - Create `.env` file with:
    ```
    NEWSAPI_KEY=your_newsapi_key_here
    GEMINI_KEY=your_gemini_key_here
    ```

**5 minutes:** Install
```bash
pip install -r requirements.txt
```

**5 minutes:** Run
```bash
streamlit run news_analyzer.py
```

**30 minutes:** Test it
- Search "technology", "bitcoin", "ai news"
- Try sorting by credibility/sentiment
- Check summaries work
- Take screenshots

**30 minutes:** Learn how it works
- Read CODE_EXPLANATION.txt
- Understand the 4 APIs
- Read ARCHITECTURE.txt

**30 minutes:** Prepare presentation
- Read PRESENTATION_SCRIPT.txt
- Write down 5 key talking points
- Practice explaining it to someone

---

## 💡 WHAT THIS APP DOES

```
You: "Search tech news"
     ↓
API gets 10 real articles
     ↓
Program analyzes each:
  ✅ Credibility: Is this source trustworthy?
  ✅ Sentiment: Is this positive or negative?
  ✅ Summary: What's the key point?
     ↓
Beautiful cards showing everything
```

**In 30 seconds, not 3 hours!**

---

## 🎯 YOUR PRESENTATION (Tomorrow)

**Opening (30 seconds):**
> "In a world of misinformation, how do you know what's real? 
> We built an AI system that analyzes articles and tells you 
> if they're trustworthy."

**Demo (5 minutes):**
- Open app
- Search for something trending
- Show credibility scores (BBC: 95%, random blog: 35%)
- Show AI summaries (Gemini wrote these)
- Show sentiment analysis (happy vs sad articles)
- Sort by credibility

**Explanation (2 minutes):**
- "Uses 4 different APIs working together"
- "Checks source reputation"
- "Analyzes language patterns"
- "Uses Google's AI for summaries"

**Why it's impressive:**
- Built in one night ✓
- Uses 4 different APIs ✓
- Has AI built in ✓
- Solves a real problem ✓
- Actually works ✓

---

## 🔑 THE 4 MAGIC INGREDIENTS

### 1. **NewsAPI** (Gets the news)
- Fetches real articles from 10,000 sources
- Free, requires API key
- Takes 2 seconds for 10 articles

### 2. **Gemini API** (Writes summaries)
- Google's advanced AI
- Reads 500-word article, writes 2-sentence summary
- Takes 1-2 seconds per article

### 3. **TextBlob** (Reads emotions)
- Analyzes if text is positive/negative/neutral
- Instant (no API call)
- Based on word choice

### 4. **Custom Code** (Checks trustworthiness)
- Database of source credibility (BBC=95%, etc.)
- Analyzes language patterns (exclamation marks, caps, etc.)
- Combines both for final score

---

## 🛠️ TROUBLESHOOTING

**"API key not found"**
→ Is .env file in same folder as news_analyzer.py?
→ Did you paste keys correctly?

**"Network error"**
→ Check your internet
→ Or show screenshots instead

**"App is slow"**
→ Turn off "Generate AI Summaries"
→ Or search same thing twice (uses cache)

**"Summaries look weird"**
→ That's normal - AI isn't perfect
→ Just mention it and move on

**More help?**
→ See PRESENTATION_CHECKLIST.txt
