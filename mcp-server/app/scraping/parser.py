"""Extract readable text from HTML pages."""

from urllib.parse import urlparse

from bs4 import BeautifulSoup


def extract_article(html: str, url: str, max_chars: int = 6000) -> dict:
    """Return structured JSON: title, source, url, content."""
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    main = soup.find("main") or soup.find("article") or soup.body
    paragraphs: list[str] = []
    if main:
        for node in main.find_all(["p", "h1", "h2", "h3", "li"]):
            text = " ".join(node.get_text(" ", strip=True).split())
            if len(text) > 40:
                paragraphs.append(text)

    content = "\n".join(paragraphs) if paragraphs else main.get_text("\n", strip=True) if main else ""
    content = content[:max_chars]

    return {
        "title": title or "Sans titre",
        "source": urlparse(url).netloc,
        "url": url,
        "content": content,
    }


def extract_search_results(html: str, base_url: str, limit: int = 5) -> list[dict]:
    """Parse simple link lists from a search/results page."""
    soup = BeautifulSoup(html, "html.parser")
    results: list[dict] = []

    for link in soup.find_all("a", href=True):
        href = link["href"]
        if not href.startswith("http"):
            continue
        if urlparse(href).netloc not in urlparse(base_url).netloc:
            continue
        title = " ".join(link.get_text(" ", strip=True).split())
        if len(title) < 20:
            continue
        results.append({"title": title, "url": href})
        if len(results) >= limit:
            break

    return results
