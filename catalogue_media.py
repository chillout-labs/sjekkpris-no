"""Display only supplied facts and public images; never fetch with a read key."""

import html
import json
from html.parser import HTMLParser
import os
import re
from urllib.parse import urlsplit


def public_image_url(value):
    if not isinstance(value, str) or any(c.isspace() for c in value):
        return False
    try:
        url = urlsplit(value)
        origin = urlsplit(os.environ.get("CHILLOUT_ORIGIN", ""))
        if url.scheme != "https" or url.username or url.password or url.fragment:
            return False
        if url.netloc.lower() == origin.netloc.lower() and re.fullmatch(r"/images/[A-Za-z0-9_-]{43}", url.path):
            return not url.query or bool(re.fullmatch(r"w=[1-9][0-9]{0,3}", url.query))
        # Property-stated images live on this property's public domain.
        return url.netloc.lower() in {"sjekkpris.no", "www.sjekkpris.no"} and bool(
            re.fullmatch(r"/[A-Za-z0-9/_ .%-]+\.(?:webp|png|jpe?g|avif)", url.path, re.I)
        ) and not url.query
    except ValueError:
        return False


def image_markup(image, name, *, sizes, eager=False):
    if not isinstance(image, dict) or not public_image_url(image.get("url")):
        return ""
    variants = {}
    for item in image.get("variants") or []:
        width = item.get("width")
        if isinstance(width, int) and 0 < width <= 9999 and public_image_url(item.get("url")):
            variants[width] = item["url"]
    srcset = ", ".join(f"{url} {width}w" for width, url in sorted(variants.items()))
    responsive = f' srcset="{html.escape(srcset, quote=True)}" sizes="{html.escape(sizes, quote=True)}"' if srcset else ""
    return (f'<img src="{html.escape(image["url"], quote=True)}" alt="{html.escape(name, quote=True)}"'
            f'{responsive} loading="{"eager" if eager else "lazy"}" decoding="async" referrerpolicy="no-referrer">')


def category_markup(categories, *, full=False, show_primary=True):
    if not isinstance(categories, dict):
        return ""
    primary = categories.get("primary")
    if not primary or not primary.get("active", True):
        return ""
    name = html.escape(primary.get("display_name") or primary.get("name") or "")
    result = f'<p class="sp-product-category">Kategori: {name}</p>' if show_primary else ""
    if full:
        path = " › ".join(item.get("display_name") or item["name"] for item in primary.get("path", []))
        result += f'<details><summary>Vis hele kategorien</summary><p>{html.escape(path)}</p>'
        additional = [item for item in categories.get("additional", []) if item.get("active", True)]
        if additional:
            result += '<p>Også kategorisert som:</p><ul>' + ''.join(
                f'<li>{html.escape(item.get("display_name") or item["name"])}</li>' for item in additional
            ) + '</ul>'
        result += '</details>'
    return result


def without_public_image_attributes(text):
    """Only the origin-host rule permits validated img src/srcset attributes.

    Credential/internal-ID rules must still inspect the original whole text.
    Product JSON-LD may repeat an already displayed, validated image. No other
    JSON field, script, link, CSS or text receives an exception.
    """
    class DisplayedImages(HTMLParser):
        def __init__(self):
            super().__init__()
            self.sources = set()

        def handle_starttag(self, tag, attrs):
            if tag == "img":
                sources = [value for name, value in attrs if name == "src"]
                if len(sources) == 1 and public_image_url(sources[0]):
                    self.sources.add(sources[0])

    displayed = DisplayedImages()
    displayed.feed(text)
    displayed.close()

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON member")
            result[key] = value
        return result

    def product_image(data):
        try:
            document = json.loads(data, object_pairs_hook=unique_object)
        except (ValueError, RecursionError):
            return data
        if (isinstance(document, dict)
                and document.get("@context") == "https://schema.org"
                and document.get("@type") == "Product"
                and isinstance(document.get("image"), str)
                and document["image"] in displayed.sources):
            document["image"] = ""
            return json.dumps(document, ensure_ascii=False)
        return data

    def allowed(name, value):
        if name == "src":
            return public_image_url(value)
        if name != "srcset" or value is None:
            return False
        items = value.split(",")
        return bool(items) and all(
            len(parts := item.strip().split()) == 2
            and public_image_url(parts[0]) and re.fullmatch(r"[1-9][0-9]{0,3}w", parts[1])
            for item in items
        )

    class ImagesOnly(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.output = []
            self.product_json = False

        def handle_starttag(self, tag, attrs):
            raw = self.get_starttag_text()
            if tag == "script":
                self.product_json = attrs == [("type", "application/ld+json")]
            if tag == "img":
                # Parse attribute boundaries before exempting values: text like
                # src="..." inside onload/data-src is not an image source.
                raw = "<img" + "".join(
                    f' {name}="{html.escape("" if allowed(name, value) else value or "", quote=True)}"'
                    for name, value in attrs
                ) + ">"
            self.output.append(raw)

        def handle_startendtag(self, tag, attrs):
            self.handle_starttag(tag, attrs)
            if tag == "script":
                self.product_json = False

        def handle_endtag(self, tag):
            if tag == "script":
                self.product_json = False
            self.output.append(f"</{tag}>")

        def handle_data(self, data):
            self.output.append(product_image(data) if self.product_json else data)

        def handle_comment(self, data):
            self.output.append("<!--" + data + "-->")

        def handle_entityref(self, name):
            self.output.append("&" + name + ";")

        def handle_charref(self, name):
            self.output.append("&#" + name + ";")

        def handle_decl(self, decl):
            self.output.append("<!" + decl + ">")

        def handle_pi(self, data):
            self.output.append("<?" + data + ">")

        def unknown_decl(self, data):
            self.output.append(data)

    parser = ImagesOnly()
    parser.feed(text)
    parser.close()
    return "".join(parser.output)
