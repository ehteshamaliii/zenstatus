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

## 🌐 Production Deployment

### Webuzo / cPanel Deployment

This guide covers deploying ZenStatus on a production server using Webuzo or similar Python hosting environments.

#### 1. Upload Files to Server

Upload your repository to your server's application directory:
```bash
/home/zenstatus/public_html/zen/
├── check_sites.py
├── wsgi.py
├── requirements.txt
├── static/
└── venv/ (will be created)
```

#### 2. Create Virtual Environment

SSH into your server and create a virtual environment:
```bash
cd /home/zenstatus/public_html/zen
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

Install required packages in the virtual environment:
```bash
pip install -r requirements.txt
pip install gunicorn
```

#### 4. Configure Webuzo Python Application

In your Webuzo control panel, configure the Python application with these settings:

| Setting | Value |
|---------|-------|
| **Port** | 30000 (or your assigned port) |
| **Application Name** | Zen Status |
| **Deployment Domain** | zen.alluredigital.org |
| **Base Application URL** | zen.alluredigital.org/ |
| **Application Path** | /home/zenstatus/public_html/zen |
| **Application Type** | Python 3 |
| **Application Startup File** | wsgi.py |
| **Start Command** | `./venv/bin/gunicorn --bind 127.0.0.1:30000 --timeout 1200 --workers 2 wsgi:app` |
| **Stop Command** | `pkill -f gunicorn` |

#### 5. Environment Variables (Optional)

Add any required environment variables in Webuzo:
- `port`: 30000

#### 6. Start the Application

Start your application using the Webuzo interface or manually:
```bash
cd /home/zenstatus/public_html/zen
./venv/bin/gunicorn --bind 127.0.0.1:30000 --timeout 1200 --workers 2 wsgi:app
```

**Important**: The `--timeout 1200` flag sets worker timeout to 20 minutes, which is essential for SEO audits with 500+ pages. Without this, Gunicorn will kill workers after 30 seconds.

#### 7. Configure Reverse Proxy (If Needed)

Ensure your web server (Apache/Nginx) is configured to proxy requests to your application port. This is usually handled automatically by Webuzo.

#### Production Tips

- **Process Management**: Use Supervisor or systemd for automatic restarts
- **Workers**: For better performance, add workers: `--workers 4`
- **Timeout**: For large audits (500+ pages), use `--timeout 1200` (20 minutes) or higher for very large sites
- **Logging**: Enable Gunicorn logging: `--access-logfile access.log --error-logfile error.log`
- **Security**: Always use HTTPS in production
- **Updates**: Pull latest changes and restart: 
  ```bash
  git pull origin main
  pkill -f gunicorn
  ./venv/bin/gunicorn --bind 127.0.0.1:30000 --timeout 1200 --workers 2 wsgi:app
  ```

#### Troubleshooting `ERR_INCOMPLETE_CHUNKED_ENCODING`

If you get this error on large SEO audits (500+ pages):

1. **Increase Gunicorn timeout**: Add `--timeout 1200` (20 minutes) or `--timeout 1500` (25 minutes) to your start command
2. **Check proxy timeout**: Ensure Apache/Nginx proxy timeout is also increased:
   ```apache
   # Apache
   ProxyTimeout 1200
   
   # Nginx
   proxy_read_timeout 1200s;
   ```
3. **Monitor logs**: Check `error.log` for worker timeout messages
4. **Break into batches**: For very large sites (1000+ pages), consider setting a lower max_pages limit

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

## 👨‍💻 Author

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
