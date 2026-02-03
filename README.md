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
  <a href="#-production-deployment">Deployment</a> •
  <a href="#-usage">Usage</a> •
  <a href="#-api">API</a> •
  <a href="#-themes">Themes</a> •
  <a href="#-seo-metrics-analyzed">SEO Metrics</a> •
  <a href="#-tech-stack">Tech Stack</a> •
  <a href="#-contributing">Contributing</a>
</p>

---

## ✨ Features

### 🔍 Website Status Checking
- **Bulk URL checking** — Check multiple websites simultaneously
- **Real-time progress** — Stream results as they complete with live progress bar
- **Response metrics** — Status codes, response times, and availability
- **File upload** — Import URLs from `.txt` files

### 📊 SEO Auditing
- **Comprehensive analysis** — Title tags, meta descriptions, heading hierarchy (H1-H4), word count, and more
- **SEO scoring** — Each page receives a 0-100 score based on SEO best practices
- **Sitemap crawling** — Automatically discover and crawl XML sitemaps (up to 10,000 pages)
- **Duplicate detection** — Identify duplicate pages with visual indicators
- **Issue prioritization** — Top issues highlighted for quick action
- **Heading hierarchy** — Visual breakdown of H1, H2, H3, H4 tag counts

### 🔎 Filter & Sort
- **Filter by status** — View all pages, only issues, good scores (70+), or poor scores (<70)
- **Sort options** — Sort by score (ascending/descending) or by number of issues
- **Per-site grouping** — Results organized by domain with site-level statistics

### 📜 Audit History
- **Persistent storage** — Previous audits saved to localStorage
- **Quick reload** — Click any saved audit to reload results instantly
- **Auto-cleanup** — Keeps last 10 audits, automatically manages storage limits

### 🎨 Modern UI/UX
- **Multiple themes** — Serenity (Classic Blue), Sage (Earth Tones), Rose (Soft Pink)
- **Responsive design** — Works on desktop and mobile
- **Print-ready reports** — Clean print layout for client deliverables
- **Dynamic favicon** — Favicon color changes based on selected theme
- **Toast notifications** — Non-intrusive feedback for all actions
- **Loading states** — Progress bar with percentage during audits

### 📤 Export Options
- **JSON export** — Full data for programmatic use
- **CSV export** — Spreadsheet-compatible format with all metrics
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

#### Variables

Replace these placeholders with your actual values:
- `{APP_PATH}` — Your application directory (e.g., `/home/username/public_html/app`)
- `{DOMAIN}` — Your domain name (e.g., `seo.example.com`)
- `{PORT}` — Your assigned port number (e.g., `30000`)

#### 1. Upload Files to Server

Upload your repository to your server's application directory:
```bash
{APP_PATH}/
├── check_sites.py
├── wsgi.py
├── requirements.txt
├── static/
└── venv/ (will be created)
```

#### 2. Create Virtual Environment

SSH into your server and create a virtual environment:
```bash
cd {APP_PATH}
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
| **Port** | `{PORT}` |
| **Application Name** | ZenStatus |
| **Deployment Domain** | `{DOMAIN}` |
| **Base Application URL** | `{DOMAIN}/` |
| **Application Path** | `{APP_PATH}` |
| **Application Type** | Python 3 |
| **Application Startup File** | wsgi.py |
| **Start Command** | `./venv/bin/gunicorn --bind 127.0.0.1:{PORT} --timeout 1200 --workers 2 wsgi:app` |
| **Stop Command** | `pkill -f gunicorn` |

#### 5. Environment Variables (Optional)

Add any required environment variables in Webuzo:
- `port`: `{PORT}`

#### 6. Start the Application

Start your application using the Webuzo interface or manually:
```bash
cd {APP_PATH}
./venv/bin/gunicorn --bind 127.0.0.1:{PORT} --timeout 1200 --workers 2 wsgi:app
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
2. Or click **"Upload File"** to import URLs from a `.txt` file
3. Click **"Check Status"**
4. View results with status codes, response times, and availability

### SEO Audit
1. Enter target URLs (e.g., `example.com` or `https://example.com`)
2. Or upload a file containing URLs
3. Enable **"Crawl sitemap automatically"** to discover all pages
4. Optionally set a **max pages limit** (up to 10,000)
5. Click **"SEO Audit"**
6. Review grouped results by site with detailed metrics and SEO scores

### Filter & Sort Results
After an SEO audit completes:
- **Filter buttons** — Show All, Issues Only, Good (70+), or Poor (<70)
- **Sort dropdown** — Default order, Score (Low→High), Score (High→Low), or Most Issues
- Filters and sorts apply within each site group

### Audit History
- Completed audits are automatically saved to browser storage
- Click the **History** dropdown to view saved audits
- Click any saved audit to reload its results
- Click **"Clear History"** to remove all saved audits

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
| **H2 Count** | Number of H2 tags on page | 1 or more |
| **H3 Count** | Number of H3 tags on page | Varies |
| **H4 Count** | Number of H4 tags on page | Varies |
| **Word Count** | Total words in body content | 300+ words |
| **Internal Links** | Links to same domain | Varies |
| **External Links** | Links to other domains | Varies |
| **Images Missing Alt** | Images without alt text | 0 |
| **Robots Meta** | Robots directive | index, follow |
| **Canonical URL** | Canonical link element | Should exist |
| **HTTPS** | Secure connection | Required |
| **Response Time** | Server response time | < 2 seconds |

### SEO Score Calculation

Each page receives a score from 0-100 based on:
- **Title optimization** — Length and presence
- **Meta description** — Length and presence
- **Heading structure** — Proper H1 usage
- **Content depth** — Word count
- **Image accessibility** — Alt text coverage
- **Technical SEO** — Canonical, robots, HTTPS

| Score Range | Rating |
|-------------|--------|
| 90-100 | Excellent |
| 70-89 | Good |
| 50-69 | Needs Work |
| 0-49 | Poor |

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
├── check_sites.py          # Main Flask application & SEO auditing logic
├── wsgi.py                 # WSGI entry point for production
├── requirements.txt        # Python dependencies
├── LICENSE                 # MIT License
├── README.md               # Documentation
├── templates/
│   ├── base.html           # Main HTML template
│   └── partials/           # Reusable template components
│       ├── input_section.html
│       ├── loading.html
│       ├── results_section.html
│       └── seo_results.html
└── static/
    ├── logo.svg            # Application logo
    ├── css/
    │   ├── base.css        # Core styles
    │   ├── components.css  # UI component styles
    │   ├── themes.css      # Theme definitions
    │   └── responsive.css  # Mobile responsive styles
    └── js/
        ├── storage.js      # LocalStorage wrapper (ZenStorage)
        ├── themes.js       # Theme switching & favicon
        ├── ui.js           # Toast notifications, modals, loading states
        ├── api.js          # Server communication & result rendering
        ├── export.js       # JSON/CSV export functionality
        └── main.js         # App initialization, history, filter/sort
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
