#!/usr/bin/env python3
"""Update the "Latest from jetworks.io" list in README.md from the site's Atom feed.

Standard library only. Replaces everything between the BLOG markers in README.md.
"""
import html
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

FEED = "https://jetworks.io/feed.xml"
README = "README.md"
COUNT = 5
START, END = "<!-- blog:start -->", "<!-- blog:end -->"
NS = {"a": "http://www.w3.org/2005/Atom"}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-readme-updater (+https://jetworks.io)"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def latest(feed_xml, count):
    root = ET.fromstring(feed_xml)
    posts = []
    for e in root.findall("a:entry", NS):
        title = html.unescape((e.findtext("a:title", default="", namespaces=NS) or "").strip())
        link_el = e.find("a:link", NS)
        link = link_el.get("href") if link_el is not None else ""
        when = (e.findtext("a:updated", default="", namespaces=NS) or "")[:10]
        if title and link:
            posts.append((when, title, link))
    posts.sort(key=lambda p: p[0], reverse=True)
    return posts[:count]


def render(posts):
    lines = []
    for when, title, link in posts:
        try:
            nice = datetime.strptime(when, "%Y-%m-%d").strftime("%d %b %Y")
        except ValueError:
            nice = when
        lines.append(f"- [{title}]({link}) / {nice}")
    return "\n".join(lines)


def main():
    posts = latest(fetch(FEED), COUNT)
    if not posts:
        print("no posts found; README left unchanged")
        return 0
    text = open(README, encoding="utf-8").read()
    if START not in text or END not in text:
        print("markers not found in README.md", file=sys.stderr)
        return 1
    new = re.sub(re.escape(START) + r".*?" + re.escape(END),
                 START + "\n" + render(posts) + "\n" + END, text, flags=re.S)
    if new != text:
        open(README, "w", encoding="utf-8").write(new)
        print("README updated")
    else:
        print("no change")
    return 0


if __name__ == "__main__":
    sys.exit(main())
