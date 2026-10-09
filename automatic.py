"""Three approved daily site-only English posts, bounded delayed execution."""
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import uuid
from brand import render_free_design
from ledger import Ledger
import site_content
from instagram_connection import connect
HOURS=(9,11,17)
ACCOUNT='istanbul.highlights'

def due_slot(now):
    local=now.astimezone(ZoneInfo('Europe/Istanbul'))
    for hour in reversed(HOURS):
        slot=local.replace(hour=hour,minute=0,second=0,microsecond=0)
        if slot<=local<slot+timedelta(minutes=90): return slot
    return None

def select_content(slot,history):
    urls=site_content.discover()
    if not urls: raise ValueError('No English place pages found.')
    # A stable daily shuffle, then prefer places not used recently.
    seed=slot.date().isoformat()
    urls.sort(key=lambda u:hashlib.sha256((seed+u).encode()).hexdigest())
    last_place={};last_image={}
    for record in sorted(history,key=lambda r:r['scheduled_at']):
        if record['status'] in ('published','uploading','uncertain','preparing','ready'):
            last_place[record.get('source_url')]=record['scheduled_at']
            last_image[record.get('image_url')]=record['scheduled_at']
    urls.sort(key=lambda u:last_place.get(u,''))
    for url in urls[:12]:
        try:
            item=site_content.place(url)
            item['images'].sort(key=lambda u:last_image.get(u,''))
            for image_url in item['images']:
                try: content=site_content.photo(image_url)
                except (ValueError,OSError,site_content.requests.RequestException):continue
                return dict(item,image_url=image_url),content
        except (ValueError,OSError,site_content.requests.RequestException):continue
    raise ValueError('No usable site photo and English description available.')

def run(now=None,ledger=None,client_factory=None):
    now=now or datetime.now(timezone.utc);slot=due_slot(now)
    if slot is None: print('Outside publication window.');return
    # Never build or consume a slot until the intended account is connected.
    if os.getenv('IG_USERNAME')!=ACCOUNT: raise RuntimeError('Connect the istanbul.highlights account first.')
    if not os.getenv('IG_PASSWORD'): raise RuntimeError('Instagram connection missing.')
    ledger=ledger if ledger is not None else Ledger()
    job_id=str(uuid.uuid5(uuid.NAMESPACE_URL,'istanbul-highlights:'+slot.isoformat()))
    if ledger.get(job_id): print('This publication slot already has a record; no duplicate.');return
    item,content=select_content(slot,ledger.rows())
    post=dict(id=job_id,scheduled_at=slot.isoformat(),created_at=now.isoformat(),status='preparing',title=item['title'],caption=site_content.caption(item),source_url=item['source_url'],image_url=item['image_url'],instagram_url=None,error=None)
    # Commit reservation before any Instagram action. Failure stops publication.
    if not ledger.insert(post):return
    stage='preparing'
    try:
        with tempfile.TemporaryDirectory(prefix='highlights-auto-') as folder:
            raw=Path(folder)/'site.jpg';final=Path(folder)/'branded.jpg';raw.write_bytes(content)
            render_free_design(raw,final,item['title'])
            client=connect(client_factory)
            # Persist uploading BEFORE the remote upload, so retries cannot duplicate.
            if not ledger.change(job_id,'preparing',status='uploading'):return
            stage='uploading';media=client.photo_upload(str(final),post['caption'])
            if not media or not getattr(media,'pk',None) or not getattr(media,'code',None):raise RuntimeError('Publication unconfirmed.')
            ledger.change(job_id,'uploading',status='published',media_id=str(media.pk),instagram_url='https://www.instagram.com/p/'+media.code+'/',published_at=datetime.now(timezone.utc).isoformat())
            print('Instagram publication confirmed.')
    except Exception:
        # A failed state write leaves the earlier reservation intact: still no retry.
        try:ledger.change(job_id,stage,status='uncertain' if stage=='uploading' else 'failed',error='Check Instagram before any retry.' if stage=='uploading' else 'Publication did not start. Check connection and source.')
        except Exception:pass
        raise RuntimeError('Automatic publication stopped; inspect status.') from None

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--preview',action='store_true');parser.add_argument('--url',default='https://istanbulhighlights.com/en/ayasofya');args=parser.parse_args()
    if args.preview:
        item=site_content.place(args.url);photo=site_content.photo(item['images'][0]);Path('preview').mkdir(exist_ok=True)
        raw=Path('preview/source.jpg');raw.write_bytes(photo);render_free_design(raw,'preview/post.jpg',item['title']);Path('preview/caption.txt').write_text(site_content.caption(item));print('preview/post.jpg; preview/caption.txt. No Instagram publication.')
    else:run()
