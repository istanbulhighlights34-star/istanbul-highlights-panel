"""Only English place pages and same-site photos. Never search external media."""
from html.parser import HTMLParser
from urllib.parse import urljoin,urlsplit,quote
import re
import io
import requests
from PIL import Image
ORIGIN='https://istanbulhighlights.com'
SKIP={'guides','about','contact','privacy','terms','affiliate-disclosure','photo-credits','istanbul-3-day-itinerary','historic-peninsula','galata-beyoglu','bosphorus-besiktas'}
class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.lang='';self.meta={};self.links=[];self.images=[];self.heading=[];self.paragraphs=[];self.h=0;self.p=None;self.ignore=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='html': self.lang=a.get('lang','')
        if tag=='meta': self.meta[a.get('property',a.get('name',''))]=a.get('content','')
        if tag=='a': self.links.append(a.get('href',''))
        if tag=='img': self.images.append(a.get('src',''))
        if tag=='h1': self.h+=1
        if tag=='p': self.p=[]
        if tag in ('script','style'): self.ignore+=1
    def handle_endtag(self,tag):
        if tag=='h1': self.h=max(0,self.h-1)
        if tag=='p' and self.p is not None: self.paragraphs.append(' '.join(''.join(self.p).split()));self.p=None
        if tag in ('script','style'): self.ignore=max(0,self.ignore-1)
    def handle_data(self,data):
        if self.ignore: return
        if self.h: self.heading.append(data)
        if self.p is not None: self.p.append(data)

def site_url(url):
    u=urlsplit(urljoin(ORIGIN,url))
    if u.scheme!='https' or u.hostname!='istanbulhighlights.com' or u.port not in (None,443) or u.username or u.password:
        raise ValueError('Only istanbulhighlights.com URLs are allowed.')
    return u._replace(path=quote(u.path,safe='/%-._~'),fragment='').geturl()
def fetch(url,limit=2*1024*1024):
    url=site_url(url)
    for _ in range(4):
        with requests.get(url,timeout=(10,30),stream=True,allow_redirects=False) as r:
            if r.is_redirect: url=site_url(urljoin(url,r.headers['Location']));continue
            r.raise_for_status();data=bytearray()
            for chunk in r.iter_content(65536):
                data.extend(chunk)
                if len(data)>limit: raise ValueError('Site file exceeds size limit.')
            return bytes(data)
    raise ValueError('Too many redirects.')
def parse(html):
    p=Page();p.feed(html);return p

def discover(html=None):
    p=parse(html if html is not None else fetch(ORIGIN+'/en').decode('utf-8'))
    links=[]
    for link in p.links:
        try: url=site_url(link)
        except ValueError: continue
        path=urlsplit(url).path.rstrip('/');slug=path.split('/')[-1]
        if path.startswith('/en/') and path.count('/')==2 and slug not in SKIP and url not in links: links.append(url)
    return links

def place(url,html=None):
    url=site_url(url)
    if not urlsplit(url).path.startswith('/en/'): raise ValueError('English place page required.')
    p=parse(html if html is not None else fetch(url).decode('utf-8'))
    if p.lang.lower() not in ('en','en-us','en-gb') or p.meta.get('og:type')!='article': raise ValueError('English article required.')
    title=' '.join(''.join(p.heading).split())
    summary=next((x for x in p.paragraphs if 60<=len(x)<=450),p.meta.get('description',''))
    if not title or not summary or len(summary)>500: raise ValueError('Usable title and short description required.')
    images=[]
    for candidate in [p.meta.get('og:image',''),*p.images]:
        if not candidate: continue
        try: image=site_url(candidate)
        except ValueError: continue
        if urlsplit(image).path.startswith('/images/') and urlsplit(image).path.lower().endswith(('.jpg','.jpeg','.png','.webp')) and image not in images: images.append(image)
    if not images: raise ValueError('No site-hosted photo available.')
    return dict(title=title,summary=summary,source_url=url,images=images)
def short_description(item):
    # Keep source facts and English prose, with at most two complete sentences.
    text=' '.join(item['summary'].split())
    sentences=re.split(r'(?<=[.!?])\s+',text)
    selected=[]
    for sentence in sentences[:2]:
        if len(' '.join([*selected,sentence]))>450:break
        selected.append(sentence)
    result=' '.join(selected)
    if not result: raise ValueError('A concise English description is required.')
    if result[-1] not in '.!?': result+='.'
    return result

def hashtags(item):
    import unicodedata
    title=unicodedata.normalize('NFKD',item['title']).encode('ascii','ignore').decode()
    place_tag=''.join(re.findall(r'[A-Za-z0-9]+',title))
    if not place_tag:raise ValueError('A place hashtag is required.')
    slug=urlsplit(item['source_url']).path.lower()
    extra='#IstanbulTravel'
    if 'muzesi' in slug or 'museum' in slug: extra='#IstanbulMuseums'
    elif 'camii' in slug:extra='#IstanbulArchitecture'
    elif 'sarayi' in slug or 'ayasofya' in slug:extra='#IstanbulHistory'
    elif 'bosphorus' in slug or 'bogaz' in slug:extra='#Bosphorus'
    return f'#istanbul #istanbulhighlights #events #{place_tag} {extra}'

def caption(item):
    return f"{short_description(item)}\n\nDiscover more at istanbulhighlights.com\n{item['source_url']}\n\n{hashtags(item)}"
def photo(url):
    data=fetch(url,15*1024*1024)
    with Image.open(io.BytesIO(data)) as image:
        if image.width*image.height>40000000 or min(image.size)<320: raise ValueError('Photo dimensions unsuitable.')
        image.verify()
    return data
