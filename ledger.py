"""Public, credential-free publication metadata; atomic GitHub commits persist it."""
import base64
import json
import os
import requests
REPOSITORY='istanbulhighlights34-star/istanbul-highlights-panel'
PATH='publication-state.json'
class Ledger:
    def __init__(self,token=None):
        self.token=token if token is not None else os.getenv('GITHUB_TOKEN','')
        self.sha=None;self.posts=[];self.load()
    def load(self):
        headers={'Accept':'application/vnd.github+json'}
        if self.token: headers['Authorization']='Bearer '+self.token
        r=requests.get(f'https://api.github.com/repos/{REPOSITORY}/contents/{PATH}',headers=headers,params={'ref':'main'},timeout=30)
        if r.status_code==404: self.sha=None;self.posts=[];return
        r.raise_for_status();body=r.json();self.sha=body['sha'];self.posts=json.loads(base64.b64decode(body['content']))['posts']
    def save(self):
        if not self.token: raise RuntimeError('Publication ledger write token missing.')
        payload=json.dumps({'version':1,'posts':self.posts},ensure_ascii=False,indent=2)
        body={'message':'Update automatic publication status','content':base64.b64encode(payload.encode()).decode(),'branch':'main'}
        if self.sha: body['sha']=self.sha
        r=requests.put(f'https://api.github.com/repos/{REPOSITORY}/contents/{PATH}',headers={'Authorization':'Bearer '+self.token,'Accept':'application/vnd.github+json'},json=body,timeout=30)
        r.raise_for_status();self.sha=r.json()['content']['sha']
    def rows(self): return list(self.posts)
    def get(self,job_id):
        return next((p for p in self.posts if p['id']==job_id),None)
    def insert(self,post):
        if self.get(post['id']): return False
        self.posts.append(post);self.save();return True
    def change(self,job_id,old,**data):
        post=self.get(job_id)
        if not post or post['status']!=old:return False
        post.update(data);self.save();return True
