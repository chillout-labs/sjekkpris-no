"""Check local beta links, fragments and lazily fetched card resources offline.

Usage: python tools/check_design_links.py SITE_ROOT [BETA_PREFIX]
Example: python tools/check_design_links.py _beta_test /beta/
No external links or affiliate clickouts are fetched.
"""
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
from urllib.parse import unquote, urljoin, urlsplit


class Document(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.ids=Counter()
        self.links=[]
        self.inline_json=[]
        self.json_parts=None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        data=dict(attrs)
        if tag=='script' and data.get('type')=='application/json':
            self.json_parts=[]
        if data.get('id'):
            self.ids[data['id']]+=1
        for key in ('href','src'):
            if data.get(key):
                self.links.append(data[key])

    def handle_data(self,data):
        if self.json_parts is not None:
            self.json_parts.append(data)

    def handle_endtag(self,tag):
        if tag=='script' and self.json_parts is not None:
            self.inline_json.append(json.loads(''.join(self.json_parts)))
            self.json_parts=None


def check(root, prefix='/'):
    root=Path(root).resolve()
    scope=root/prefix.strip('/')
    errors=[]
    documents={path:Document(path.read_text(encoding='utf-8')) for path in scope.rglob('*.html')}
    if not documents:
        return ['No HTML pages found in '+str(scope)]
    targets=[]
    for path,doc in documents.items():
        errors.extend(f'{path.relative_to(root)}: duplicate id {key}' for key,count in doc.ids.items() if count>1)
        targets.extend((path,url) for url in doc.links)
    def json_links(value, path):
        if isinstance(value,dict):
            for key,item in value.items():
                if key=='html' and isinstance(item,str):
                    targets.extend((path,url) for url in Document(item).links)
                elif key in ('url','card') and isinstance(item,str):
                    targets.append((path,item))
                else:
                    json_links(item,path)
        elif isinstance(value,list):
            for item in value:
                json_links(item,path)
    for path,doc in documents.items():
        for value in doc.inline_json:
            json_links(value,path)
    for path in scope.rglob('*.json'):
        json_links(json.loads(path.read_text(encoding='utf-8')),path)
    for source,url in targets:
        parts=urlsplit(url)
        if parts.scheme or parts.netloc:
            continue
        resolved=urlsplit(urljoin('/'+source.relative_to(root).as_posix(),url))
        destination=(root/unquote(resolved.path).lstrip('/')).resolve()
        if not destination.is_relative_to(root):
            errors.append(f'{source.relative_to(root)}: outside site {url}')
            continue
        if destination.is_dir():
            destination=destination/'index.html'
        if not destination.is_file():
            errors.append(f'{source.relative_to(root)}: missing target {url}')
        elif resolved.fragment and destination.suffix=='.html':
            doc=documents.get(destination)
            if doc is None:
                doc=Document(destination.read_text(encoding='utf-8'))
                documents[destination]=doc
            if unquote(resolved.fragment) not in doc.ids:
                errors.append(f'{source.relative_to(root)}: missing fragment {url}')
    return errors


if __name__=='__main__':
    errors=check(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else '/')
    if errors:
        raise SystemExit('\n'.join(errors))
    print('Beta local links, fragments, IDs and deferred card resources verified.')
