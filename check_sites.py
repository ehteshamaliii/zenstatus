"""
ZenStatus - Website SEO Auditor
================================
A comprehensive SEO audit tool that checks websites for common SEO issues.

SEO Coverage (based on industry standards):
- Technical SEO: Crawlability, HTTPS, response time, robots, canonical, redirects
- On-page SEO: Title, meta description, H1-H6 hierarchy, word count, images
- Content Analysis: Word count, thin content detection, heading structure
- Link Analysis: Internal/external link counts, broken link detection
- Site Analysis: Sitemap.xml detection, robots.txt analysis
"""

from flask import Flask, render_template, request, jsonify, Response
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import urlparse, urljoin
import xml.etree.ElementTree as ET
import re
import json
import time
import gzip
import hashlib

app = Flask(__name__)

# Cache for site-level data (robots.txt, sitemap status)
site_cache = {}


def update_site_cache_sitemap(base_url, sitemap_url, url_count=0):
    """
    Update the site cache to indicate that a sitemap was successfully found.
    This is called after successfully crawling a sitemap to prevent false "No sitemap" warnings.
    """
    parsed = urlparse(base_url)
    domain = f"{parsed.scheme}://{parsed.netloc}"
    
    # Get existing cache or create new entry
    if domain in site_cache:
        site_cache[domain]['has_sitemap'] = True
        site_cache[domain]['sitemap_url'] = sitemap_url
        if url_count > 0:
            site_cache[domain]['sitemap_url_count'] = url_count
    else:
        # Create a new cache entry if it doesn't exist
        site_cache[domain] = {
            'has_robots_txt': False,
            'robots_txt_content': '',
            'robots_rules': [],
            'has_sitemap': True,
            'sitemap_url': sitemap_url,
            'sitemap_url_count': url_count
        }


def get_site_info(base_url, timeout=10):
    """
    Get site-level information: robots.txt and sitemap.xml status.
    Results are cached per domain.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    parsed = urlparse(base_url)
    domain = f"{parsed.scheme}://{parsed.netloc}"
    
    if domain in site_cache:
        return site_cache[domain]
    
    result = {
        'has_robots_txt': False,
        'robots_txt_content': '',
        'robots_rules': [],
        'has_sitemap': False,
        'sitemap_url': '',
        'sitemap_url_count': 0
    }
    
    # Check robots.txt
    try:
        robots_url = f"{domain}/robots.txt"
        resp = requests.get(robots_url, timeout=timeout, headers=headers)
        if resp.status_code == 200 and 'text' in resp.headers.get('Content-Type', ''):
            result['has_robots_txt'] = True
            result['robots_txt_content'] = resp.text[:2000]  # First 2000 chars
            
            # Parse basic rules
            rules = []
            for line in resp.text.split('\n'):
                line = line.strip()
                if line.startswith('Disallow:') or line.startswith('Allow:'):
                    rules.append(line)
                elif line.startswith('Sitemap:'):
                    sitemap_match = line.split(':', 1)
                    if len(sitemap_match) > 1:
                        result['sitemap_url'] = sitemap_match[1].strip()
            result['robots_rules'] = rules[:20]  # First 20 rules
    except:
        pass
    
    # Check sitemap.xml
    try:
        sitemap_url = result['sitemap_url'] or f"{domain}/sitemap.xml"
        resp = requests.get(sitemap_url, timeout=timeout, headers=headers)
        if resp.status_code == 200:
            result['has_sitemap'] = True
            result['sitemap_url'] = sitemap_url
            # Count URLs in sitemap
            try:
                root = ET.fromstring(resp.content)
                url_count = sum(1 for child in root if 'url' in child.tag.lower() or 'sitemap' in child.tag.lower())
                result['sitemap_url_count'] = url_count
            except:
                pass
    except:
        pass
    
    site_cache[domain] = result
    return result


def check_link_status(url, timeout=5):
    """Quick check if a link is broken (returns status code)."""
    try:
        resp = requests.head(url, timeout=timeout, allow_redirects=True)
        return resp.status_code
    except:
        try:
            resp = requests.get(url, timeout=timeout, allow_redirects=True, stream=True)
            return resp.status_code
        except:
            return 0


def get_redirect_chain(url, timeout=10, max_redirects=10):
    """Track redirect chain for a URL."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    chain = []
    current_url = url
    
    for _ in range(max_redirects):
        try:
            resp = requests.head(current_url, timeout=timeout, allow_redirects=False, headers=headers)
            chain.append({
                'url': current_url,
                'status': resp.status_code
            })
            
            if resp.status_code in (301, 302, 303, 307, 308):
                location = resp.headers.get('Location')
                if location:
                    current_url = urljoin(current_url, location)
                else:
                    break
            else:
                break
        except:
            chain.append({'url': current_url, 'status': 0})
            break
    
    return chain


def check_website_status(url, timeout=10):
    """Check the status of a website and verify it's actually working."""
    try:
        start_time = datetime.now()
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        response_text = response.text.lower()
        if 'error establishing a database connection' in response_text:
            return {
                'url': url,
                'status_code': response.status_code,
                'status_message': 'DB Connection Error',
                'response_time': f"{response_time:.2f}s"
            }
        
        if 'fatal error' in response_text or 'database error' in response_text:
            return {
                'url': url,
                'status_code': response.status_code,
                'status_message': 'Site Error',
                'response_time': f"{response_time:.2f}s"
            }
        
        return {
            'url': url,
            'status_code': response.status_code,
            'status_message': 'Online' if response.status_code < 400 else 'Error',
            'response_time': f"{response_time:.2f}s"
        }
    except requests.exceptions.Timeout:
        return {
            'url': url,
            'status_code': 'N/A',
            'status_message': 'Timeout',
            'response_time': 'N/A'
        }
    except requests.exceptions.ConnectionError:
        return {
            'url': url,
            'status_code': 'N/A',
            'status_message': 'Connection Error',
            'response_time': 'N/A'
        }
    except Exception:
        return {
            'url': url,
            'status_code': 'N/A',
            'status_message': 'Error',
            'response_time': 'N/A'
        }


def audit_website(url, timeout=15, max_retries=2):
    """
    Perform a comprehensive SEO audit for a single URL.
    
    Covers:
    - Technical SEO: HTTP status, HTTPS, response time, robots, canonical, viewport, structured data
    - On-page SEO: Title, meta description, H1-H6 hierarchy, word count
    - Social/Open Graph: OG title, description, image
    - Content: Word count, thin content detection
    - Links: Internal/external link analysis
    - Images: Alt text check
    - Accessibility: Language attribute
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # Default error response
    error_result = {
        'url': url,
        'status_code': 'N/A',
        'status_message': 'Error',
        'response_time': 'N/A',
        'title': '',
        'title_length': 0,
        'meta_description': '',
        'meta_description_length': 0,
        'h1_count': 0,
        'h2_count': 0,
        'h3_count': 0,
        'h4_count': 0,
        'h5_count': 0,
        'h6_count': 0,
        'h1_samples': [],
        'canonical': '',
        'robots': '',
        'word_count': 0,
        'internal_links': 0,
        'external_links': 0,
        'broken_links': 0,
        'broken_link_samples': [],
        'images_missing_alt': 0,
        'images_no_dimensions': 0,
        'images_not_lazy': 0,
        'total_images': 0,
        'https': False,
        'url_length': len(url),
        'url_has_underscores': '_' in url,
        'redirect_count': 0,
        'redirect_chain': [],
        # Site-level info
        'has_robots_txt': False,
        'has_sitemap': False,
        'sitemap_url_count': 0,
        # New fields
        'has_viewport': False,
        'has_lang': False,
        'lang': '',
        'has_og_tags': False,
        'og_title': '',
        'og_description': '',
        'og_image': '',
        'has_twitter_cards': False,
        'has_schema': False,
        'schema_types': [],
        # Performance / Core Web Vitals proxies
        'page_size_kb': 0,
        'ttfb_estimate': 0,
        'render_blocking_count': 0,
        'inline_css_count': 0,
        'external_scripts': 0,
        'warnings': []
    }

    try:
        # Retry logic for resilience
        attempt = 0
        while True:
            try:
                start_time = datetime.now()
                response = requests.get(url, timeout=timeout, allow_redirects=True, headers=headers)
                response_time = (datetime.now() - start_time).total_seconds()
                break
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                attempt += 1
                if attempt >= max_retries:
                    raise
                time.sleep(1.0 * attempt)

        soup = BeautifulSoup(response.text, 'html.parser')

        # Check HTTPS
        is_https = response.url.startswith('https://')

        # Title analysis
        title = soup.title.string.strip() if soup.title and soup.title.string else ''
        
        # Meta description
        meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
        meta_description = meta_desc_tag.get('content', '').strip() if meta_desc_tag else ''
        
        # Canonical tag
        canonical_tag = soup.find('link', rel=lambda rel: rel and 'canonical' in rel.lower())
        canonical = canonical_tag.get('href') if canonical_tag else ''
        
        # Robots meta tag
        robots_tag = soup.find('meta', attrs={'name': 'robots'})
        robots = robots_tag.get('content', '').lower().strip() if robots_tag and robots_tag.get('content') else ''
        
        # Viewport meta tag (mobile-friendliness)
        viewport_tag = soup.find('meta', attrs={'name': 'viewport'})
        has_viewport = viewport_tag is not None
        
        # Language attribute
        html_tag = soup.find('html')
        lang = html_tag.get('lang', '').strip() if html_tag else ''
        has_lang = bool(lang)
        
        # Open Graph tags
        og_title_tag = soup.find('meta', attrs={'property': 'og:title'})
        og_title = og_title_tag.get('content', '').strip() if og_title_tag else ''
        og_desc_tag = soup.find('meta', attrs={'property': 'og:description'})
        og_description = og_desc_tag.get('content', '').strip() if og_desc_tag else ''
        og_image_tag = soup.find('meta', attrs={'property': 'og:image'})
        og_image = og_image_tag.get('content', '').strip() if og_image_tag else ''
        has_og_tags = bool(og_title or og_description or og_image)
        
        # Twitter Card tags
        twitter_card_tag = soup.find('meta', attrs={'name': 'twitter:card'})
        has_twitter_cards = twitter_card_tag is not None
        
        # Structured data (Schema.org)
        schema_scripts = soup.find_all('script', attrs={'type': 'application/ld+json'})
        schema_types = []
        has_schema = len(schema_scripts) > 0
        for script in schema_scripts[:3]:  # Limit to first 3 schemas
            try:
                schema_data = json.loads(script.string) if script.string else {}
                if isinstance(schema_data, dict) and '@type' in schema_data:
                    schema_types.append(schema_data['@type'])
                elif isinstance(schema_data, list):
                    for item in schema_data[:2]:
                        if isinstance(item, dict) and '@type' in item:
                            schema_types.append(item['@type'])
            except:
                pass
        
        # Full heading hierarchy (H1-H6)
        h1_tags = [h.get_text(strip=True) for h in soup.find_all('h1')]
        h2_count = len(soup.find_all('h2'))
        h3_count = len(soup.find_all('h3'))
        h4_count = len(soup.find_all('h4'))
        h5_count = len(soup.find_all('h5'))
        h6_count = len(soup.find_all('h6'))
        
        # Word count
        word_count = len(re.findall(r'\w+', soup.get_text(' ')))
        
        # Page size
        page_size_kb = len(response.content) / 1024

        # Image analysis (enhanced)
        images = soup.find_all('img')
        total_images = len(images)
        images_missing_alt = 0
        images_no_dimensions = 0
        images_not_lazy = 0
        
        for img in images:
            # Check alt text
            if not (img.get('alt') and img.get('alt').strip()):
                images_missing_alt += 1
            # Check dimensions (width/height attributes help CLS)
            if not (img.get('width') or img.get('height')):
                images_no_dimensions += 1
            # Check lazy loading
            loading = img.get('loading', '').lower()
            if loading != 'lazy' and not img.get('fetchpriority'):
                images_not_lazy += 1
        
        # Core Web Vitals proxies
        # TTFB estimate (server response time)
        ttfb_estimate = response_time
        
        # Count render-blocking resources (non-async/defer scripts in head, CSS without media)
        head = soup.find('head')
        render_blocking_count = 0
        external_scripts = 0
        inline_css_count = 0
        
        if head:
            # Count scripts without async/defer
            for script in head.find_all('script'):
                if script.get('src'):
                    external_scripts += 1
                    if not script.get('async') and not script.get('defer'):
                        render_blocking_count += 1
            
            # Count CSS links without media query (render-blocking)
            for link in head.find_all('link', rel='stylesheet'):
                media = link.get('media', '').lower()
                if not media or media == 'all' or media == 'screen':
                    render_blocking_count += 1
            
            # Count inline styles
            inline_css_count = len(head.find_all('style'))

        # Link analysis (enhanced with broken link detection)
        parsed_base = urlparse(response.url)
        all_links = soup.find_all('a', href=True)
        internal_links = 0
        external_links = 0
        broken_links = 0
        broken_link_samples = []
        
        # Sample up to 10 internal links for broken link check
        internal_link_urls = []
        for a in all_links:
            href = a.get('href')
            parsed_href = urlparse(href)
            if not parsed_href.netloc or parsed_href.netloc == parsed_base.netloc:
                internal_links += 1
                # Build full URL for checking
                if href.startswith('/'):
                    full_url = f"{parsed_base.scheme}://{parsed_base.netloc}{href}"
                elif href.startswith('http'):
                    full_url = href
                else:
                    full_url = urljoin(response.url, href)
                if len(internal_link_urls) < 10:
                    internal_link_urls.append(full_url)
            else:
                external_links += 1
        
        # Check sample internal links for broken status (quick check)
        for link_url in internal_link_urls[:5]:  # Check first 5
            try:
                status = check_link_status(link_url, timeout=3)
                if status >= 400 or status == 0:
                    broken_links += 1
                    if len(broken_link_samples) < 3:
                        broken_link_samples.append(link_url)
            except:
                pass
        
        # Get redirect chain
        redirect_chain = get_redirect_chain(url, timeout=5)
        redirect_count = len(redirect_chain) - 1 if len(redirect_chain) > 1 else 0
        
        # Get site-level info (robots.txt, sitemap)
        site_info = get_site_info(url, timeout=5)

        # URL structure analysis
        url_length = len(url)
        url_has_underscores = '_' in urlparse(url).path

        # Generate warnings based on SEO best practices
        warnings = []
        
        # Title warnings
        if not title:
            warnings.append('Missing title')
        elif len(title) < 30:
            warnings.append('Title too short (< 30 chars)')
        elif len(title) > 60:
            warnings.append('Title too long (> 60 chars)')

        # Meta description warnings
        if not meta_description:
            warnings.append('Missing meta description')
        elif len(meta_description) < 120:
            warnings.append('Description too short (< 120 chars)')
        elif len(meta_description) > 160:
            warnings.append('Description too long (> 160 chars)')

        # H1 warnings
        if len(h1_tags) == 0:
            warnings.append('Missing H1')
        elif len(h1_tags) > 1:
            warnings.append('Multiple H1 tags (' + str(len(h1_tags)) + ')')

        # Heading hierarchy check
        if h2_count == 0 and word_count > 300:
            warnings.append('No H2 headings for content structure')

        # Technical SEO warnings
        if not canonical:
            warnings.append('No canonical tag')
        if 'noindex' in robots:
            warnings.append('Noindex set')
        if not is_https:
            warnings.append('Not using HTTPS')
        
        # Content warnings
        if images_missing_alt > 0:
            warnings.append(f'Images missing alt text ({images_missing_alt})')
        if word_count < 300:
            warnings.append('Thin content (< 300 words)')
        
        # Image optimization warnings
        if images_no_dimensions > 0 and total_images > 0:
            warnings.append(f'Images without dimensions ({images_no_dimensions}) - affects CLS')
        if images_not_lazy > 3:
            warnings.append(f'Images not lazy-loaded ({images_not_lazy})')
        
        # Broken links warning
        if broken_links > 0:
            warnings.append(f'Broken internal links found ({broken_links})')
        
        # Redirect chain warning
        if redirect_count > 1:
            warnings.append(f'Redirect chain ({redirect_count} hops)')
        
        # Site-level warnings
        if not site_info.get('has_robots_txt'):
            warnings.append('No robots.txt file')
        if not site_info.get('has_sitemap'):
            warnings.append('No sitemap.xml found')
        
        # Page size warning
        if page_size_kb > 500:
            warnings.append(f'Large page size ({page_size_kb:.0f}KB)')
        
        # URL structure warnings
        if url_length > 75:
            warnings.append('URL too long (> 75 chars)')
        if url_has_underscores:
            warnings.append('URL contains underscores (use hyphens)')

        # Response time warning
        if response_time > 3.0:
            warnings.append(f'Slow response ({response_time:.1f}s)')

        # Mobile-friendliness warning
        if not has_viewport:
            warnings.append('Missing viewport meta tag')
        
        # Language warning
        if not has_lang:
            warnings.append('Missing lang attribute on HTML')
        
        # Social/OG warnings
        if not has_og_tags:
            warnings.append('No Open Graph tags')
        
        # Schema warning
        if not has_schema:
            warnings.append('No structured data (schema.org)')
        
        # Core Web Vitals warnings
        if render_blocking_count > 3:
            warnings.append(f'Many render-blocking resources ({render_blocking_count})')
        if ttfb_estimate > 1.5:
            warnings.append(f'Slow TTFB ({ttfb_estimate:.2f}s) - consider CDN/caching')

        return {
            'url': url,
            'status_code': response.status_code,
            'status_message': 'OK' if response.status_code < 400 else 'Page Error',
            'response_time': f"{response_time:.2f}s",
            'title': title,
            'title_length': len(title),
            'meta_description': meta_description,
            'meta_description_length': len(meta_description),
            'h1_count': len(h1_tags),
            'h2_count': h2_count,
            'h3_count': h3_count,
            'h4_count': h4_count,
            'h5_count': h5_count,
            'h6_count': h6_count,
            'h1_samples': h1_tags[:3],
            'canonical': canonical,
            'robots': robots,
            'word_count': word_count,
            'internal_links': internal_links,
            'external_links': external_links,
            'broken_links': broken_links,
            'broken_link_samples': broken_link_samples,
            'images_missing_alt': images_missing_alt,
            'images_no_dimensions': images_no_dimensions,
            'images_not_lazy': images_not_lazy,
            'total_images': total_images,
            'https': is_https,
            'url_length': url_length,
            'url_has_underscores': url_has_underscores,
            'redirect_count': redirect_count,
            'redirect_chain': redirect_chain,
            # Site-level info
            'has_robots_txt': site_info.get('has_robots_txt', False),
            'has_sitemap': site_info.get('has_sitemap', False),
            'sitemap_url_count': site_info.get('sitemap_url_count', 0),
            # New fields
            'has_viewport': has_viewport,
            'has_lang': has_lang,
            'lang': lang,
            'has_og_tags': has_og_tags,
            'og_title': og_title,
            'og_description': og_description,
            'og_image': og_image,
            'has_twitter_cards': has_twitter_cards,
            'has_schema': has_schema,
            'schema_types': schema_types,
            # Performance / Core Web Vitals
            'page_size_kb': round(page_size_kb, 1),
            'ttfb_estimate': round(ttfb_estimate, 2),
            'render_blocking_count': render_blocking_count,
            'external_scripts': external_scripts,
            'inline_css_count': inline_css_count,
            'warnings': warnings
        }
    except requests.exceptions.Timeout:
        error_result['status_message'] = 'Timeout'
        error_result['warnings'] = ['Timeout']
        return error_result
    except requests.exceptions.ConnectionError:
        error_result['status_message'] = 'Connection Error'
        error_result['warnings'] = ['Connection error']
        return error_result
    except Exception:
        error_result['warnings'] = ['Unexpected error']
        return error_result


def _extract_urlset_urls(root, remaining):
    """Extract URLs from a sitemap urlset."""
    urls = []
    for child in root:
        if child.tag.endswith('url'):
            loc = None
            for sub in child:
                if sub.tag.endswith('loc'):
                    loc = sub
                    break
            
            if loc is None or not loc.text:
                continue
                
            text = loc.text.strip()
            if not text.startswith(('http://', 'https://')):
                continue
            urls.append(text)
            if len(urls) >= remaining:
                break
    return urls


def fetch_sitemap_urls(sitemap_url, max_urls=250, max_depth=15, debug=False):
    """Fetch URLs from a sitemap or sitemap index."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    collected = []
    collected_set = set()
    collected_norm_set = set()
    first_seen_norm = {}
    duplicates = []
    seen_sitemaps = set()
    queue = [(sitemap_url, 0)]
    debug_info = []
    skipped_samples = []

    def normalize_url(u):
        try:
            parsed = urlparse(u.strip())
            if parsed.scheme not in ('http', 'https'):
                return None
            netloc = parsed.netloc.lower()
            if parsed.scheme == 'http' and netloc.endswith(':80'):
                netloc = netloc[:-3]
            if parsed.scheme == 'https' and netloc.endswith(':443'):
                netloc = netloc[:-4]
            path = parsed.path or '/'
            if len(path) > 1 and path.endswith('/'):
                path = path[:-1]
            normalized = f"{parsed.scheme}://{netloc}{path}"
            if parsed.query:
                normalized += f"?{parsed.query}"
            return normalized
        except Exception:
            return None

    def record_skip(url, source, reason):
        if len(skipped_samples) < 50:
            skipped_samples.append({'url': url, 'source': source, 'reason': reason})

    def add_urls(url_list, source):
        nonlocal collected
        added = 0
        for u in url_list:
            norm = normalize_url(u)
            if not norm:
                record_skip(u, source, 'normalize-failed')
            else:
                if norm in first_seen_norm:
                    duplicates.append({'url': u, 'duplicate_of': first_seen_norm[norm], 'source': source})
                else:
                    first_seen_norm[norm] = u
            collected.append(u)
            collected_set.add(u)
            if norm:
                collected_norm_set.add(norm)
            added += 1
            if len(collected) >= max_urls:
                break
        return added

    while queue and len(collected) < max_urls:
        current_url, depth = queue.pop(0)
        if current_url in seen_sitemaps or depth > max_depth:
            continue
        seen_sitemaps.add(current_url)

        try:
            resp = requests.get(current_url, timeout=15, headers=headers)
        except (requests.exceptions.RequestException, ValueError):
            debug_info.append({
                'url': current_url,
                'depth': depth,
                'status': 'Connection Error',
                'parsed': False,
                'type': 'error',
                'found': 0
            })
            continue
            
        status = resp.status_code
        if status >= 400:
            debug_info.append({
                'url': current_url,
                'depth': depth,
                'status': status,
                'parsed': False,
                'type': 'error',
                'found': 0
            })
            continue

        content_type = resp.headers.get('Content-Type', '').lower()
        content_encoding = resp.headers.get('Content-Encoding', '').lower()
        is_gzip_hint = current_url.lower().endswith('.gz') or 'gzip' in content_type

        raw_xml = resp.content if resp.content else resp.text

        root = None
        parsed_ok = False
        parsed_type = 'unknown'
        found_count = 0
        added_now = 0

        try:
            root = ET.fromstring(raw_xml)
            parsed_ok = True
        except Exception:
            if is_gzip_hint and 'gzip' not in content_encoding:
                try:
                    decompressed = gzip.decompress(resp.content)
                    root = ET.fromstring(decompressed)
                    parsed_ok = True
                except Exception:
                    root = None

        if not parsed_ok or root is None:
            debug_info.append({
                'url': current_url,
                'depth': depth,
                'status': status,
                'parsed': False,
                'type': 'unparsed',
                'found': 0
            })
            continue

        try:
            if root.tag.endswith('sitemapindex'):
                parsed_type = 'sitemapindex'
                child_sitemaps_added = 0
                if depth < max_depth:
                    for child in root:
                        if child.tag.endswith('sitemap'):
                            loc = None
                            for sub in child:
                                if sub.tag.endswith('loc'):
                                    loc = sub
                                    break
                            if loc is not None and loc.text:
                                child_url = loc.text.strip()
                                if child_url and child_url not in seen_sitemaps and len(collected) < max_urls:
                                    queue.append((child_url, depth + 1))
                                    child_sitemaps_added += 1
                found_count = child_sitemaps_added
            elif root.tag.endswith('urlset'):
                parsed_type = 'urlset'
                new_urls = _extract_urlset_urls(root, max_urls - len(collected))
                added_now = add_urls(new_urls, current_url)
                found_count = len(new_urls)

            debug_info.append({
                'url': current_url,
                'depth': depth,
                'status': status,
                'parsed': True,
                'type': parsed_type,
                'found': found_count,
                'added': added_now
            })

        except Exception:
            continue

    result_urls = collected[:max_urls]
    if debug:
        return result_urls, {
            'sitemaps': debug_info,
            'skipped_samples': skipped_samples,
            'duplicates': duplicates
        }
    return result_urls


@app.route('/')
def index():
    """Serve the main page using Jinja2 template."""
    return render_template('base.html')


@app.route('/check', methods=['POST'])
def check_websites():
    """Check the status of submitted URLs with progress updates."""
    data = request.get_json()
    urls = data.get('urls', [])
    
    if not urls:
        return jsonify({'error': 'No URLs provided'}), 400
    
    def generate():
        results = []
        completed = 0
        total = len(urls)
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {executor.submit(check_website_status, url): url for url in urls}
            
            for future in as_completed(future_to_url):
                result = future.result()
                results.append(result)
                completed += 1
                
                progress_data = {
                    'type': 'progress',
                    'completed': completed,
                    'total': total
                }
                yield f"data: {json.dumps(progress_data)}\n\n"
        
        sorted_results = sorted(results, key=lambda x: (
            0 if x['status_message'] not in ['Online'] else 1,
            x['status_code'] if isinstance(x['status_code'], int) else 999
        ))
        
        final_data = {
            'type': 'complete',
            'results': sorted_results
        }
        yield f"data: {json.dumps(final_data)}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')


@app.route('/seo-audit', methods=['POST'])
def seo_audit():
    """Run a comprehensive SEO audit for the submitted URLs with progress updates."""
    data = request.get_json()
    urls = data.get('urls', [])
    use_sitemap = bool(data.get('use_sitemap'))
    sitemap_url = (data.get('sitemap_url') or '').strip()
    max_pages = data.get('max_pages') or 100
    try:
        max_pages = max(1, min(int(max_pages), 10000))
    except Exception:
        max_pages = 100

    sitemap_debug = []
    dup_map = {}
    original_urls = list(urls)
    
    if use_sitemap:
        if not urls:
            return jsonify({'error': 'Provide at least one URL to infer sitemap'}), 400
        
        all_crawled_urls = []
        seen_crawled = {}
        
        for base_input_url in original_urls:
            base_url = base_input_url.rstrip('/')
            target_sitemap = sitemap_url or f"{base_url}/sitemap.xml"
            sitemap_found_urls = False
            
            try:
                crawled_urls, site_debug = fetch_sitemap_urls(target_sitemap, max_pages, debug=True)
                if isinstance(site_debug, dict):
                    for d in site_debug.get('duplicates', []) or []:
                        src = d.get('url')
                        tgt = d.get('duplicate_of')
                        if src and tgt:
                            dup_map[src] = tgt
                    if 'sitemaps' in site_debug:
                        sitemap_debug.extend(site_debug['sitemaps'])
                
                if crawled_urls:
                    sitemap_found_urls = True
                    # Update the site cache to mark sitemap as found
                    update_site_cache_sitemap(base_url, target_sitemap, len(crawled_urls))
                    
                    for u in crawled_urls:
                        all_crawled_urls.append(u)
                        normalized = u.lower().rstrip('/')
                        if normalized in seen_crawled:
                            if u not in dup_map:
                                dup_map[u] = seen_crawled[normalized]
                        else:
                            seen_crawled[normalized] = u
                        
            except Exception as e:
                debug_entry = {
                    'type': 'error',
                    'status': 'Error',
                    'url': target_sitemap,
                    'note': f"Sitemap fetch failed: {str(e)}. Adding {base_input_url} to audit."
                }
                sitemap_debug.append(debug_entry)
            
            if not sitemap_found_urls:
                normalized = base_input_url.lower().rstrip('/')
                if normalized not in seen_crawled:
                    all_crawled_urls.append(base_input_url)
                    seen_crawled[normalized] = base_input_url
        
        if all_crawled_urls:
            urls = all_crawled_urls
        else:
            debug_entry = {
                'type': 'warning',
                'status': 'Empty',
                'url': 'All sitemaps',
                'note': 'No URLs found in sitemaps. Auditing entered URLs only.'
            }
            sitemap_debug.append(debug_entry)
            
    elif not urls:
        return jsonify({'error': 'No URLs provided'}), 400
    
    dup_map = dup_map if use_sitemap else {}

    def generate():
        results = []
        completed = 0
        total = len(urls)
        last_update = time.time()

        yield ": keep-alive\n\n"

        batch_size = 300
        start_index = 0
        while start_index < total:
            batch = urls[start_index:start_index + batch_size]
            pool_size = min(8, max(2, len(batch)))
            with ThreadPoolExecutor(max_workers=pool_size) as executor:
                future_to_url = {executor.submit(audit_website, url): url for url in batch}

                for future in as_completed(future_to_url):
                    if time.time() - last_update > 10:
                        yield ": keep-alive\n\n"
                        last_update = time.time()
                    
                    result = future.result()
                    if dup_map:
                        dup_of = dup_map.get(result.get('url'))
                        if dup_of:
                            result['duplicate_of'] = dup_of
                            if 'warnings' not in result:
                                result['warnings'] = []
                            if 'Duplicate URL' not in result['warnings']:
                                result['warnings'].append('Duplicate URL')
                    results.append(result)
                    completed += 1

                    progress_data = {
                        'type': 'progress',
                        'completed': completed,
                        'total': total
                    }
                    yield f"data: {json.dumps(progress_data)}\n\n"
                    last_update = time.time()
            start_index += batch_size

        sorted_results = sorted(results, key=lambda x: (
            0 if x.get('status_message') == 'OK' else 1,
            x.get('status_code') if isinstance(x.get('status_code'), int) else 999
        ))

        final_data = {
            'type': 'complete',
            'results': sorted_results,
            'sitemap_debug': sitemap_debug
        }
        yield f"data: {json.dumps(final_data)}\n\n"

    return Response(generate(), mimetype='text/event-stream')


if __name__ == '__main__':
    import sys
    
    production = '--production' in sys.argv
    
    if production:
        print("\n" + "="*60)
        print("🌐 ZenStatus SEO Auditor - Production Mode")
        print("="*60)
        print("\n✓ Running on http://127.0.0.1:5001")
        print("\n⏹  Press CTRL+C to stop the server\n")
        print("="*60 + "\n")
        app.run(debug=False, host='127.0.0.1', port=5001, threaded=True)
    else:
        print("\n" + "="*60)
        print("🌐 ZenStatus SEO Auditor - Development Mode")
        print("="*60)
        print("\n📍 Open your browser: http://127.0.0.1:5000")
        print("\n💡 Features:")
        print("   - Complete SEO audit with scoring")
        print("   - H1-H6 heading analysis")
        print("   - HTTPS & security checks")
        print("   - Content quality analysis")
        print("   - Export to JSON/CSV/Markdown")
        print("\n⏹  Press CTRL+C to stop the server\n")
        print("="*60 + "\n")
        app.run(debug=True, host='0.0.0.0', port=5000)
