"""Use the account password and an optional existing private session."""
import json
import os
ACCOUNT='istanbul.highlights'
def connect(client_factory=None):
    if os.getenv('IG_USERNAME',ACCOUNT)!=ACCOUNT or not os.getenv('IG_PASSWORD'):
        raise RuntimeError('Required Instagram account password is missing.')
    if client_factory is None:
        from instagrapi import Client
        client_factory=Client
    client=client_factory()
    session=os.getenv('IG_SESSION','').strip()
    if session:
        settings=json.loads(session)
        if not isinstance(settings,dict):raise ValueError('Invalid session format.')
        client.set_settings(settings)
    client.login(ACCOUNT,os.environ['IG_PASSWORD'])
    if client.account_info().username.lower()!=ACCOUNT:raise RuntimeError('Instagram account mismatch.')
    return client
if __name__=='__main__':
    try:
        connect()
        print('Connection verified for @istanbul.highlights. No publication was made.')
    except Exception as exc:
        print('Connection not verified. Error type: '+type(exc).__name__)
        raise SystemExit(1) from None
