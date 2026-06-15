# Doodle Search 🔍

A **fast, semantic search engine** built with Flask and BERT-style embeddings. Search across multiple CSV datasets (English, Arabic, and health records) using natural language or exact keyword matching with intelligent autocomplete.

---

## ✨ Features

- **Semantic Search**: Uses BERT embeddings (sentence-transformers) for meaning-aware search results
- **Multi-Language Support**: Handles English and Arabic text with language-specific preprocessing
- **Smart Autocomplete**: Real-time suggestions and sentence completions as you type
- **Fuzzy Matching**: Handles typos and misspellings with automatic spell correction
- **Dark Mode**: Toggle between light and dark themes with persistent preferences
- **Responsive Design**: Google-like UI that works on desktop and mobile
- **Dual Inference Modes**: 
  - Local embeddings (default, no downloads needed)
  - Remote inference via Hugging Face Inference API (optional)
- **Fast Startup**: Lazy-loading of models and embeddings—no blocking initialization

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, Flask
- **NLP**: sentence-transformers (BERT), NLTK, qalsadi
- **Frontend**: HTML, CSS (CSS variables for theming), Vanilla JavaScript
- **Data**: CSV files (pandas-compatible), lazy preprocessing
- **Embedding Models**: all-MiniLM-L6-v2 (default) or custom via HF Inference API

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or later
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/AdelElgabry202301510/doodle-search.git
   cd doodle-search
   ```

2. **Create a virtual environment**
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   
   # macOS/Linux
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app**
   ```bash
   python app.py
   ```
   
   The app will be available at `http://localhost:5000`

---

## 📖 Usage

### Search
1. Open the home page
2. Type a label, keyword, or full sentence
3. View autocomplete suggestions in real-time
4. Press Enter or click the search button
5. Click on any result to view the full document

### Toggle Theme
Click the moon icon in the header to switch between light and dark modes. Your preference is saved automatically.

### Using Remote Embeddings (Optional)
To use Hugging Face Inference API instead of local embeddings:

```bash
# Windows PowerShell
$env:USE_HF_INFERENCE = "true"
$env:HF_API_TOKEN = "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"
python app.py

# macOS/Linux
export USE_HF_INFERENCE=true
export HF_API_TOKEN=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
python app.py
```

Get your HF token from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

---

## 📁 Project Structure

```
doodle-search/
├── app.py                      # Flask entry point
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── search_app/
│   ├── data_loader.py         # CSV loading, preprocessing, autocomplete
│   └── search_engine.py       # Semantic search, ranking, embeddings
├── templates/
│   ├── base.html              # Base layout (header, theme toggle, footer)
│   ├── home.html              # Search page
│   ├── results.html           # Search results page
│   └── article.html           # Full document view
├── static/
│   ├── css/style.css          # Responsive styling, dark theme
│   ├── js/autocomplete.js     # Client-side autocomplete logic
│   └── images/logo.png        # Doodle logo
└── data/
    ├── arabic.csv            # Arabic dataset
    ├── english.csv           # English dataset
    └── health.csv            # Health records dataset
```

---

## 🔧 How It Works

### Search Flow

1. **User Input**: User types in search bar
2. **Autocomplete**: `DataLoader` returns label matches and sentence completions via `/autocomplete` endpoint
3. **Query Submission**: Form submits to `/search` route
4. **Preprocessing**: Text is tokenized and lemmatized (cached for performance)
5. **Embedding**: Query is converted to BERT embedding (local or remote)
6. **Ranking**: Results ranked by semantic similarity, with keyword fallback
7. **Display**: Top results shown with highlighted query terms

### Data Loading

- **Lazy Preprocessing**: Documents preprocessed only when needed
- **Language Detection**: Arabic lemmatized via qalsadi, English via NLTK WordNetLemmatizer
- **Caching**: Lemmatization results cached to avoid recomputation
- **Limits**: Arabic processing limited (5000 rows, 1000 tokens per doc) to prevent hangs

### Performance Optimizations

- Models and embeddings loaded only on first search (lazy initialization)
- Preprocessed text cached in memory
- Autocomplete uses pre-built term pool for instant suggestions
- Fuzzy matching retried if no exact results found

---

## 🎨 UI/UX Highlights

- **Google-like Design**: Centered logo, wide search bar, clean results
- **Dark Mode**: Full CSS variable theming for seamless switching
- **Responsive**: Works on mobile, tablet, and desktop
- **Accessible**: ARIA labels, keyboard navigation, high contrast
- **Real-time Feedback**: Autocomplete updates as you type (180ms debounce)

---

## 📊 Datasets

The app comes pre-configured with three datasets:

| Dataset | Size | Language | Use Case |
|---------|------|----------|----------|
| `english.csv` | ~2000 rows | English | General text search |
| `arabic.csv` | ~5000 rows (limited) | Arabic | Arabic language search |
| `health.csv` | ~1000 rows | English | Medical/health information |

To add your own data, add a CSV file to the `data/` directory with a `text` or `content` column.

---

## 🔐 Environment Variables

---

## 🚢 Deployment

### Local Development
```bash
python app.py
```

### Production (with Gunicorn)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```
---

## 🛣️ Future Improvements

- [ ] Add persistent caching (JSON/SQLite) for embeddings
- [ ] Support for additional languages (French, Spanish, etc.)
- [ ] Full-text indexing for faster keyword search
- [ ] Advanced filters (date range, source, etc.)
- [ ] User authentication and saved searches
- [ ] Analytics and search insights dashboard
- [ ] API endpoint for programmatic search

---

## 🤝 Contributing

Contributions are welcome! Feel free to:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👤 Author

**Adel** - Building intelligent search tools with Python & AI

- GitHub: [@AdelElgabry202301510](https://github.com/AdelElgabry202301510)

---

## 📞 Support

If you have questions or encounter issues:

1. Check the [Issues](https://github.com/AdelElgabry202301510/doodle-search/issues) page
2. Open a new issue with details about your problem
3. Include environment info: Python version, OS, error messages

---

## 🎓 Learning Resources

- [Sentence Transformers Documentation](https://www.sbert.net/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [BERT Explained](https://huggingface.co/blog/bert-101)
- [CSS Variables](https://developer.mozilla.org/en-US/docs/Web/CSS/--*)

---

Made with ❤️ for efficient semantic search

If you want to use the Hugging Face-hosted models, no local model training is required; the app will download and cache them automatically.

NO-DOWNLOAD / OFFLINE DEFAULT

By default the application will NOT download model weights from the network. The app will only load models if you have explicitly saved them under the local `models/english_model` or `models/arabic_model` directories.

Behavior summary:
- If `models/english_model` and/or `models/arabic_model` exist, the app will load them and enable semantic search.
- If neither local model directory exists, the app will NOT attempt to download anything and will run using keyword-based search and label matching only.
- If you *do* want the app to download from Hugging Face, tell me and I can add an explicit option to enable network model loading or call the Hugging Face Inference API (which may require an API token).

Remote (no-download) semantic mode via Hugging Face Inference API

If you want the app to use your Hugging Face-hosted models without downloading weights locally, enable the remote inference option:

1. Set environment variables before starting the app:

```powershell
setx HF_API_TOKEN "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"
setx USE_HF_INFERENCE "true"
```

2. On startup, if `USE_HF_INFERENCE` is true and `HF_API_TOKEN` is set, the app will call the Hugging Face Inference API's embeddings endpoint to compute embeddings remotely for documents and queries. No model files are downloaded locally.

Notes:
- Remote inference requires network access and consumes credits on Hugging Face (or requires appropriate plan). It may be slower than local inference and subject to rate limits.
- For large corpora, embeddings are computed in batches at startup and cached in memory; you can add persistence if you want to avoid repeated embedding calls across restarts.
