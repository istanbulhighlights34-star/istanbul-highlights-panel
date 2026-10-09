"""Local-only preview: random private password, generated fresh at startup."""
import os
import secrets
from pathlib import Path
os.chdir(Path(__file__).resolve().parent)
os.environ.setdefault('PANEL_PASSWORD',secrets.token_urlsafe(14))
os.environ.setdefault('PANEL_SESSION_SECRET',secrets.token_urlsafe(48))
os.environ['LOCAL_PREVIEW']='true'
from panel.app import app
print('Panel: http://127.0.0.1:5057',flush=True)
print('Yerel giriş şifresi: '+os.environ['PANEL_PASSWORD'],flush=True)
app.run(host='127.0.0.1',port=5057,debug=False)
