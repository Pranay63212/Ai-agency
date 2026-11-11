"""Find a business's public contact email on its own website.

Looks at the homepage and a few common pages (contact, about), and prefers addresses on the
company's own domain. Only reads a handful of pages per site, slowly, like a person would.
"""

import re
import time
import urllib.error
import urllib.parse
import urllib.request

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PAGES = ["", "contact", "contact-us", "about", "about-us"]
SKIP = ("example.", "sentry", "wixpress", "godaddy", "domain.com", "yourname", "email.com",
        "@2x", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")
PREFERRED = ("owner", "info", "office", "contact", "service", "sales", "hello", "estimates")
USER_AGENT = "Mozilla/5.0 (compatible; contact-finder/1.0)"


def normalize_site(site: str) -> str:
    site = (site or "").strip()
    if not site:
        return ""
    if not site.startswith(("http://", "https://")):
        site = "https://" + site
    return site.rstrip("/") + "/"


def _fetch(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if "html" not in (resp.headers.get("Content-Type") or "html"):
            return ""
        return resp.read(1_500_000).decode("utf-8", "ignore")


def extract_emails(html: str) -> list[str]:
    html = urllib.parse.unquote(html).replace("&#64;", "@").replace("[at]", "@").replace("(at)", "@")
    found = []
    for e in EMAIL_RE.findall(html):
        e = e.strip(".").lower()
        if not any(s in e for s in SKIP) and e not in found:
            found.append(e)
    return found


def best_email(emails: list[str], site: str) -> str:
    """Prefer the company's own domain, then a general inbox like info@ or office@."""
    domain = urllib.parse.urlparse(normalize_site(site)).netloc.removeprefix("www.")
    def score(e):
        local, _, dom = e.partition("@")
        return (dom != domain and not dom.endswith("." + domain),
                not any(local.startswith(p) for p in PREFERRED))
    return sorted(emails, key=score)[0] if emails else ""


def find_email(site: str, fetch=_fetch, pause: float = 1.0) -> tuple[str, str]:
    """Returns (email, note)."""
    base = normalize_site(site)
    if not base:
        return "", "no website"
    emails: list[str] = []
    for page in PAGES:
        try:
            emails += [e for e in extract_emails(fetch(urllib.parse.urljoin(base, page))) if e not in emails]
        except (urllib.error.URLError, TimeoutError, ValueError, OSError):
            continue
        finally:
            if pause:
                time.sleep(pause)
        if emails and page:  # found on a contact/about page: good enough
            break
    return (best_email(emails, base), "found") if emails else ("", "none on site")
