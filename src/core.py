import sqlite3, re, json, time, urllib.parse, datetime, pathlib
from bs4 import BeautifulSoup
import requests

SCHEMA = '''
CREATE TABLE IF NOT EXISTS websites(id INTEGER PRIMARY KEY, domain TEXT UNIQUE NOT NULL, status TEXT DEFAULT 'NEW', contact_email TEXT, source_url TEXT, assigned_mailbox TEXT, thread_id TEXT, message_id TEXT, sent_at TEXT, followups INTEGER DEFAULT 0, last_reply_at TEXT, last_error TEXT, updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS offers(id INTEGER PRIMARY KEY, website_id INTEGER NOT NULL REFERENCES websites(id), currency TEXT, standard_price REAL, crypto_price REAL, links INTEGER, sponsored TEXT, turnaround TEXT, insertion TEXT, evidence TEXT, raw_reply TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, website_id INTEGER, kind TEXT, details TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS suppression(email TEXT PRIMARY KEY, reason TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS mailboxes(address TEXT PRIMARY KEY, enabled INTEGER DEFAULT 1, sent_today INTEGER DEFAULT 0, day TEXT);
CREATE UNIQUE INDEX IF NOT EXISTS idx_mail_thread ON websites(assigned_mailbox,thread_id) WHERE thread_id IS NOT NULL;
'''
def db_open(path):
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    db=sqlite3.connect(path); db.row_factory=sqlite3.Row; db.executescript(SCHEMA); return db

def normalize_domain(value):
    value=value.strip()
    if not value: raise ValueError('empty domain')
    if not re.match(r'^https?://',value,re.I): value='https://'+value
    host=(urllib.parse.urlsplit(value).hostname or '').lower().rstrip('.')
    if not host or '.' not in host or not re.fullmatch(r'[a-z0-9.-]+',host): raise ValueError('invalid domain')
    return host.removeprefix('www.')

def import_domains(db, domains):
    count=0
    for d in domains:
        try:
            cur=db.execute('INSERT OR IGNORE INTO websites(domain) VALUES (?)',(normalize_domain(d),))
            count+=cur.rowcount
        except ValueError: pass
    db.commit(); return count

def research(domain,timeout=12):
    # Public pages only; no bypassing access controls or scraping private contacts.
    base='https://'+normalize_domain(domain)
    session=requests.Session(); session.headers['User-Agent']='GuestPostResearchBot/1.0'
    paths=['/','/contact','/contact-us','/advertise','/write-for-us','/about']
    for path in paths:
        url=base+path
        try:
            res=session.get(url,timeout=timeout,allow_redirects=True)
            if res.status_code!=200 or 'text/html' not in res.headers.get('content-type',''): continue
            soup=BeautifulSoup(res.text[:500000],'html.parser')
            for a in soup.select('a[href^="mailto:"]'):
                email=urllib.parse.unquote(a['href'][7:].split('?')[0]).strip().lower()
                if re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):
                    return {'email':email,'source_url':res.url,'status':'CONTACT_FOUND'}
        except requests.RequestException: continue
    return {'email':None,'source_url':None,'status':'NEEDS_BROWSER_RESEARCH'}

def extract_prices(text):
    # Conservative parser: ambiguity goes to AI/human review.
    money=re.findall(r'(?i)(USD|EUR|GBP|\$|€|£)\s*(\d+(?:\.\d{1,2})?)|\b(\d+(?:\.\d{1,2})?)\s*(USD|EUR|GBP)\b',text)
    parsed=[]
    for a,b,c,d in money:
        cur={'$':'USD','€':'EUR','£':'GBP'}.get(a,a) if a else d.upper()
        parsed.append((cur,float(b or c)))
    currencies={x[0] for x in parsed}
    result={'currency':next(iter(currencies)) if len(currencies)==1 else None,'standard_price':None,'crypto_price':None,'links':None,'sponsored':None,'turnaround':None,'insertion':None,'needs_review':True,'evidence':text[:1500]}
    if len(parsed)==1:
        result['standard_price']=parsed[0][1]; result['needs_review']=False
    links=re.search(r'(?i)\b(\d+)\s*(?:do[ -]?follow\s+)?links?\b',text)
    if links: result['links']=int(links.group(1))
    if re.search(r'(?i)\b(no link insertions?|do not accept link insertions?)\b',text): result['insertion']='No'
    return result

def record_offer(db,website_id,reply,parsed):
    db.execute('INSERT INTO offers(website_id,currency,standard_price,crypto_price,links,sponsored,turnaround,insertion,evidence,raw_reply) VALUES (?,?,?,?,?,?,?,?,?,?)',(website_id,parsed.get('currency'),parsed.get('standard_price'),parsed.get('crypto_price'),parsed.get('links'),parsed.get('sponsored'),parsed.get('turnaround'),parsed.get('insertion'),parsed.get('evidence'),reply))
    db.execute("UPDATE websites SET status=?,last_reply_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP WHERE id=?",('NEEDS_REVIEW' if parsed.get('needs_review') else 'PRICE_RECEIVED',website_id));db.commit()

def followup_due(sent_at,followups,days,now=None):
    if followups>=len(days) or not sent_at: return False
    now=now or datetime.datetime.now(datetime.timezone.utc)
    sent=datetime.datetime.fromisoformat(sent_at.replace('Z','+00:00'))
    if sent.tzinfo is None: sent=sent.replace(tzinfo=datetime.timezone.utc)
    return now>=sent+datetime.timedelta(days=days[followups])
