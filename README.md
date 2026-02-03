# ZenStatus

<p align="center">
  <img src="static/logo.svg" alt="ZenStatus Logo" width="80" height="80">
</p>

<p align="center">
  <strong>Website Status & SEO Auditing. Reimagined for clarity and calm.</strong>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-usage">Usage</a> •
  <a href="#-api">API</a> •
  <a href="#-themes">Themes</a> •
  <a href="#-contributing">Contributing</a>
</p>

---

## ✨ Features

### 🔍 Website Status Checking
- **Bulk URL checking** — Check multiple websites simultaneously
- **Real-time progress** — Stream results as they complete
- **Response metrics** — Status codes, response times, and availability

### 📊 SEO Auditing
- **Comprehensive analysis** — Title tags, meta descriptions, H1 tags, word count, and more
- **Sitemap crawling** — Automatically discover and crawl XML sitemaps
- **Duplicate detection** — Identify duplicate pages with visual indicators
- **Issue prioritization** — Top issues highlighted for quick action

### 🎨 Modern UI/UX
- **Multiple themes** — Serenity (Classic Blue), Sage (Earth Tones), Rose (Soft Pink)
- **Responsive design** — Works on desktop and mobile
- **Print-ready reports** — Clean print layout for client deliverables
- **Dynamic favicon** — Favicon color changes based on selected theme

### 📤 Export Options
- **JSON export** — Full data for programmatic use
- **CSV export** — Spreadsheet-compatible format
- **Per-site CSV** — Separate CSV files for each audited domain
- **Print report** — Professional PDF-ready output

---

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/ehteshamaliii/zenstatus.git
   cd zenstatus
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python check_sites.py
   ```

5. **Open in browser**
   ```
   http://localhost:5000
   ```

---

## 📖 Usage

### Basic Status Check
1. Enter one or more URLs in the textarea (one per line)
2. Click **"Check Status"**
3. View results with status codes, response times, and availability

### SEO Audit
1. Enter target URLs (e.g., `example.com` or `https://example.com`)
2. Enable **"Crawl sitemap automatically"** to discover all pages
3. Optionally set a **max pages limit** (up to 10,000)
4. Click **"SEO Audit"**
5. Review grouped results by site with detailed metrics

### URL Formats Supported
```
https://example.com
http://example.com
example.com          # Auto-prefixed with https://
www.example.com      # Auto-prefixed with https://
```

### Sitemap Options
- **Auto-discovery** — Automatically finds `/sitemap.xml` or `/sitemap_index.xml`
- **Custom sitemap URL** — Specify a custom sitemap location
- **Nested sitemaps** — Supports sitemap index files with multiple sitemaps
- **Gzip support** — Handles compressed `.xml.gz` sitemaps

---

## 🔌 API

ZenStatus provides streaming API endpoints for integration.

### POST `/check`
Check website status for multiple URLs.

**Request:**
```json
{
  "urls": ["https://example.com", "https://example.org"]
}
```

**Response:** Server-Sent Events (SSE) stream with progress and results.

### POST `/seo-audit`
Run SEO audit on URLs with optional sitemap crawling.

**Request:**
```json
{
  "urls": ["https://example.com"],
  "use_sitemap": true,
  "sitemap_url": "",
  "max_pages": 100
}
```

**Response:** Server-Sent Events (SSE) stream with progress and results.

---

## 🎨 Themes

ZenStatus includes three carefully crafted themes:

| Theme | Description | Primary Color |
|-------|-------------|---------------|
| **Serenity** | Classic Blue & Cool Grays | `#0F4C81` |
| **Sage** | Desert Sage & Earth Tones | `#768a73` |
| **Rose** | Rose Quartz & Soft Grays | `#B76E79` |

Theme preference is saved to localStorage and persists across sessions.

---

## 📊 SEO Metrics Analyzed

| Metric | Description | Recommendation |
|--------|-------------|----------------|
| **Title Length** | Characters in `<title>` tag | 50-60 characters |
| **Meta Description** | Characters in meta description | 150-160 characters |
| **H1 Count** | Number of H1 tags on page | Exactly 1 |
| **Word Count** | Total words in body content | 300+ words |
| **Internal Links** | Links to same domain | Varies |
| **External Links** | Links to other domains | Varies |
| **Images Missing Alt** | Images without alt text | 0 |
| **Robots Meta** | Robots directive | index, follow |
| **Canonical URL** | Canonical link element | Should exist |

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask
- **HTTP Client:** Requests
- **HTML Parsing:** BeautifulSoup4
- **XML Parsing:** ElementTree
- **Concurrency:** ThreadPoolExecutor
- **Frontend:** Vanilla JavaScript, CSS Custom Properties
- **Fonts:** Montserrat, Outfit (Google Fonts)

---

## 📁 Project Structure

```
zenstatus/
├── check_sites.py      # Main Flask application
├── requirements.txt    # Python dependencies
├── static/
│   └── logo.svg        # Application logo
└── README.md           # This file
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

---

## � Author

**Ehtesham Ali**

- GitHub: [@ehteshamaliii](https://github.com/ehteshamaliii)

---

## 🙏 Acknowledgments

- Inspired by the need for a calm, focused SEO auditing experience
- Color themes inspired by Pantone Colors of the Year
- Built with modern web standards and accessibility in mind

---

<p align="center">
  Made with ☕ and attention to detail by <a href="https://github.com/ehteshamaliii">Ehtesham Ali</a>
</p>
