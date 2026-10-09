import os
import unittest
from datetime import datetime
from unittest.mock import Mock,patch
import automatic
import site_content

HTML='<html lang="en"><head><meta property="og:type" content="article"><meta property="og:image" content="/images/place.jpg"></head><body><h1>Hagia Sophia</h1><p>The cultural heritage of two empires and a timeless dome at the heart of Istanbul.</p><img src="https://elsewhere.example/photo.jpg"><img src="/images/place2.jpg"></body></html>'
class MemoryLedger:
    def __init__(self):self.posts=[]
    def get(self,id):return next((p for p in self.posts if p['id']==id),None)
    def rows(self):return self.posts
    def insert(self,post):self.posts.append(dict(post));return True
    def change(self,id,old,**data):
        p=self.get(id)
        if p['status']!=old:return False
        p.update(data);return True
class AutomationTests(unittest.TestCase):
    def test_times_and_no_catchup(self):
        for utc_hour,local_hour in [(6,9),(8,11),(14,17)]:
            slot=automatic.due_slot(datetime.fromisoformat(f'2026-10-09T{utc_hour:02}:00:00+00:00'))
            self.assertEqual(slot.hour,local_hour)
        for stamp in ['2026-10-09T05:59:00+00:00','2026-10-09T07:31:00+00:00','2026-10-09T16:00:00+00:00']:
            self.assertIsNone(automatic.due_slot(datetime.fromisoformat(stamp)))
    def test_only_english_site_photos(self):
        item=site_content.place('https://istanbulhighlights.com/en/ayasofya',HTML)
        self.assertEqual(len(item['images']),2)
        self.assertIn('Discover more at istanbulhighlights.com',site_content.caption(item))
        self.assertLess(len(item['summary']),450)
        with self.assertRaises(ValueError):site_content.place('https://istanbulhighlights.com/en/x',HTML.replace('lang="en"','lang="tr"'))
        for url in ['http://istanbulhighlights.com/images/x.jpg','https://istanbulhighlights.com.evil.test/x','https://elsewhere.test/x','https://istanbulhighlights.com:444/x','https://user@istanbulhighlights.com/x']:
            with self.assertRaises(ValueError):site_content.site_url(url)
    def exercise(self,failure=False):
        ledger=MemoryLedger();client=Mock();client.account_info.return_value.username='istanbul.highlights';client.photo_upload.return_value=Mock(pk=123,code='confirmed')
        if failure:client.photo_upload.side_effect=TimeoutError()
        item=site_content.place('https://istanbulhighlights.com/en/ayasofya',HTML);item['image_url']=item['images'][0]
        now=datetime.fromisoformat('2026-10-09T06:00:00+00:00')
        env={'IG_USERNAME':'istanbul.highlights','IG_PASSWORD':'test-password','IG_SESSION':'{}'}
        with patch.dict(os.environ,env),patch('automatic.select_content',return_value=(item,b'photo')),patch('automatic.render_free_design'):
            if failure:
                with self.assertRaises(RuntimeError):automatic.run(now,ledger,lambda:client)
            else:automatic.run(now,ledger,lambda:client)
            automatic.run(now,ledger,lambda:client)
        self.assertEqual(client.photo_upload.call_count,1)
        self.assertEqual(ledger.posts[0]['status'],'uncertain' if failure else 'published')
    def test_single_publish_per_slot(self):self.exercise()
    def test_uncertain_never_retries(self):self.exercise(True)
    def test_failed_ledger_commit_never_uploads(self):
        ledger=MemoryLedger();ledger.insert=Mock(side_effect=RuntimeError('cannot commit'));client=Mock()
        item=site_content.place('https://istanbulhighlights.com/en/ayasofya',HTML);item['image_url']=item['images'][0]
        with patch.dict(os.environ,{'IG_USERNAME':'istanbul.highlights','IG_PASSWORD':'x','IG_SESSION':'{}'}),patch('automatic.select_content',return_value=(item,b'x')):
            with self.assertRaises(RuntimeError):automatic.run(datetime.fromisoformat('2026-10-09T06:00:00+00:00'),ledger,lambda:client)
        client.photo_upload.assert_not_called()
    def test_no_upload_route(self):
        from panel.app import create_app
        with patch.dict(os.environ,{'PANEL_PASSWORD':'test','PANEL_SESSION_SECRET':'test'}):
            app=create_app();app.config['SESSION_COOKIE_SECURE']=False;client=app.test_client()
            self.assertEqual(client.get('/health').status_code,200)
            self.assertEqual(client.get('/').status_code,302)
            with client.session_transaction() as session:session['owner']=True;session['csrf']='token'
            self.assertEqual(client.post('/preview',data={'csrf':'token'}).status_code,404)
            with patch('panel.app.Ledger') as ledger:
                ledger.return_value.rows.return_value=[]
                html=client.get('/').data.decode()
                self.assertIn('09:00',html);self.assertNotIn('type="file"',html)

    def test_password_only_connection_never_publishes(self):
        from instagram_connection import connect
        client=Mock();client.account_info.return_value.username='istanbul.highlights'
        with patch.dict(os.environ,{'IG_USERNAME':'istanbul.highlights','IG_PASSWORD':'test-only','IG_SESSION':''}):
            self.assertIs(connect(lambda:client),client)
        client.set_settings.assert_not_called();client.photo_upload.assert_not_called()
