#!/usr/bin/env python3
import os, re, json, datetime, pathlib
from typing import Dict, Any, List
from markdown import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape
ROOT = pathlib.Path(__file__).parent.resolve()
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
ASSETS = ROOT / "assets"
DIST = ROOT / "dist"
SITE_TITLE = "AI Markdown Blog"
SITE_DESCRIPTION = "A professional, SEO-first blog powered by Python and GitHub Pages."
SITE_URL = "https://n1s4t.github.io/ai-blog-starter/"
AUTHOR = "n1s4t"
env = Environment(loader=FileSystemLoader(str(TEMPLATES)), autoescape=select_autoescape(['html', 'xml']))
def slugify(s:str)->str:
    s=s.lower(); s=re.sub(r"[^a-z0-9\s-]","",s); s=re.sub(r"\s+","-",s).strip("-"); return s or "post"
def parse_front_matter(text:str):
    if text.startswith("---"):
        parts=text.split("---",2)
        if len(parts)>=3:
            raw, body=parts[1], parts[2].lstrip("\n")
            meta={}
            for line in raw.splitlines():
                if ":" in line:
                    k,v=line.split(":",1); meta[k.strip()]=v.strip().strip('"').strip("'")
            return meta, body
    return {}, text
def ensure_dirs():
    DIST.mkdir(exist_ok=True, parents=True); (DIST/"assets").mkdir(exist_ok=True)
    for name in ["styles.css","toggle.js","search.js","favicon.svg","gunslol.svg"]:
        (DIST/"assets"/name).write_bytes((ASSETS/name).read_bytes())
def build_posts()->List[Dict[str,Any]]:
    posts=[]
    for md_file in sorted(CONTENT.glob("*.md")):
        raw=md_file.read_text(encoding="utf-8")
        meta, body_md=parse_front_matter(raw)
        title=meta.get("title") or md_file.stem.replace("-"," ").title()
        description=meta.get("description") or (body_md.strip().splitlines()[0][:160] if body_md.strip().splitlines() else "")
        date=meta.get("date") or str(datetime.date.today())
        html=markdown(body_md, extensions=["fenced_code"])
        slug=slugify(meta.get("slug") or md_file.stem or title)
        url=f"{SITE_URL}posts/{slug}.html"
        jsonld={"@context":"https://schema.org","@type":"BlogPosting","headline":title,"datePublished":date,"author":{"@type":"Person","name":AUTHOR},"url":url,"mainEntityOfPage":url,"description":description}
        page=env.get_template("post.html").render(title=title,description=description,date=date,canonical=url,jsonld=json.dumps(jsonld, ensure_ascii=False, indent=2),body=html)
        out=(DIST/"posts"/f"{slug}.html"); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(page, encoding="utf-8")
        content_text=re.sub("<[^<]+?>"," ",html)
        posts.append({"title":title,"description":description,"date":date,"url":url,"slug":slug,"content":content_text[:5000]})
    posts.sort(key=lambda p:p.get("date",""), reverse=True); return posts
def build_index(posts):
    jsonld={"@context":"https://schema.org","@type":"Blog","name":SITE_TITLE,"url":SITE_URL,"author":{"@type":"Person","name":AUTHOR},"dateModified":str(datetime.date.today())}
    page=env.get_template("index.html").render(site_title=SITE_TITLE,site_description=SITE_DESCRIPTION,title=SITE_TITLE,description=SITE_DESCRIPTION,canonical=SITE_URL,jsonld=json.dumps(jsonld, ensure_ascii=False, indent=2),posts=posts,rss_url=SITE_URL+"feed.xml",search_js=SITE_URL+"assets/search.js",search_index_url=SITE_URL+"search_index.json")
    (DIST/"index.html").write_text(page, encoding="utf-8")
def build_search_index(posts): (DIST/"search_index.json").write_text(json.dumps(posts, ensure_ascii=False), encoding="utf-8")
def build_sitemap(posts):
    urls=[SITE_URL]+[p["url"] for p in posts]
    items="\n".join([f"  <url>\n    <loc>{u}</loc>\n    <changefreq>weekly</changefreq>\n  </url>" for u in urls])
    xml="<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"+items+"\n</urlset>\n"
    (DIST/"sitemap.xml").write_text(xml, encoding="utf-8")
def build_robots(): (DIST/"robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n", encoding="utf-8")
def build_rss(posts):
    items=[]
    for p in posts[:20]:
        items.append(f"  <item>\n    <title>{p["title"]}</title>\n    <link>{p["url"]}</link>\n    <description>{p["description"]}</description>\n    <pubDate>{p["date"]}</pubDate>\n  </item>")
    rss="<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<rss version=\"2.0\">\n<channel>\n  <title>"+SITE_TITLE+"</title>\n  <link>"+SITE_URL+"</link>\n  <description>"+SITE_DESCRIPTION+"</description>\n  <lastBuildDate>"+str(datetime.datetime.utcnow())+" UTC</lastBuildDate>\n"+ "\n".join(items) +"\n</channel>\n</rss>\n"
    (DIST/"feed.xml").write_text(rss, encoding="utf-8")
def main():
    DIST.mkdir(parents=True, exist_ok=True); ensure_dirs(); posts=build_posts(); build_index(posts); build_search_index(posts); build_sitemap(posts); build_robots(); build_rss(posts); print(f"Built {len(posts)} posts → {DIST}")
if __name__=="__main__": main()
