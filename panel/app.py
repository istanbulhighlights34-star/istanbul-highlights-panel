"""Private monitoring panel. No uploads and no manual publication endpoints."""
import functools
import hmac
import io
import os
import secrets
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import tempfile
from zoneinfo import ZoneInfo
from flask import Flask,abort,jsonify,redirect,render_template,request,send_file,session,url_for
from ledger import Ledger
from brand import render_free_design,logo
import site_content

def create_app():
    app=Flask(__name__)
    app.config.update(SECRET_KEY=os.getenv('PANEL_SESSION_SECRET'),SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SECURE=os.getenv('LOCAL_PREVIEW')!='true',SESSION_COOKIE_SAMESITE='Strict',PERMANENT_SESSION_LIFETIME=3600,MAX_CONTENT_LENGTH=16384)
    attempts=defaultdict(list)
    def csrf():
        session.setdefault('csrf',secrets.token_urlsafe(32));return session['csrf']
    app.jinja_env.globals.update(csrf=csrf)
    app.jinja_env.filters['istanbul_time']=lambda v:datetime.fromisoformat(v.replace('Z','+00:00')).astimezone(ZoneInfo('Europe/Istanbul')).strftime('%d.%m.%Y %H:%M') if v else '—'
    @app.before_request
    def checks():
        if request.path=='/health':return
        if not app.secret_key or not os.getenv('PANEL_PASSWORD'):return 'Panel giriş ayarları tamamlanmadı.',503
        if request.method=='POST':
            token=request.form.get('csrf','')
            if not token or not hmac.compare_digest(token,session.get('csrf','')):abort(403)
    @app.after_request
    def headers(response):
        response.headers.update({'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','X-Frame-Options':'DENY','Referrer-Policy':'no-referrer','Content-Security-Policy':"default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self'; frame-ancestors 'none'"})
        return response
    def protected(fn):
        @functools.wraps(fn)
        def wrapper(*a,**kw):
            if not session.get('owner'):return redirect(url_for('login'))
            return fn(*a,**kw)
        return wrapper
    @app.get('/health')
    def health():return jsonify(status='ok')
    @app.route('/login',methods=['GET','POST'])
    def login():
        error=None
        if request.method=='POST':
            ip=request.remote_addr or 'unknown';now=time.monotonic();attempts[ip]=[t for t in attempts[ip] if now-t<600]
            if len(attempts[ip])>=5:return render_template('login.html',error='10 dakika sonra tekrar deneyin.'),429
            attempts[ip].append(now)
            if hmac.compare_digest(request.form.get('password','').encode(),os.environ['PANEL_PASSWORD'].encode()):
                session.clear();session['owner']=True;session.permanent=True;csrf();attempts.pop(ip,None);return redirect('/')
            error='Panel şifresi doğru değil.'
        return render_template('login.html',error=error)
    @app.post('/logout')
    @protected
    def logout():session.clear();return redirect('/login')
    @app.get('/')
    @protected
    def index():
        try:posts=sorted(Ledger(token='').rows(),key=lambda p:p['scheduled_at'],reverse=True)[:30];error=None
        except Exception:posts=[];error='Yayın kayıtlarına şu an ulaşılamıyor.'
        return render_template('index.html',posts=posts,error=error)
    @app.get('/preview.jpg')
    @protected
    def preview():
        # Fixed site page, no arbitrary URLs or external photos supplied by visitors.
        try:
            item=site_content.place('https://istanbulhighlights.com/en/ayasofya');content=site_content.photo(item['images'][0])
            with tempfile.TemporaryDirectory() as folder:
                raw=Path(folder)/'source.jpg';final=Path(folder)/'final.jpg';raw.write_bytes(content);render_free_design(raw,final,item['title']);result=final.read_bytes()
            return send_file(io.BytesIO(result),mimetype='image/jpeg')
        except Exception:return 'Site önizlemesi şu an alınamıyor.',503
    return app
app=create_app()
