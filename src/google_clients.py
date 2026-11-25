"""Authorized Google APIs. Never place credentials in prompts or the repository."""
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES=['https://www.googleapis.com/auth/gmail.send','https://www.googleapis.com/auth/gmail.readonly','https://www.googleapis.com/auth/spreadsheets']
def authorize(account_label,client_secret='secrets/client_secret.json',token_dir='secrets/tokens'):
    Path(token_dir).mkdir(parents=True,exist_ok=True)
    path=Path(token_dir)/(account_label+'.json')
    creds=Credentials.from_authorized_user_file(str(path),SCOPES) if path.exists() else None
    if creds and creds.expired and creds.refresh_token: creds.refresh(Request())
    if not creds or not creds.valid:
        flow=InstalledAppFlow.from_client_secrets_file(client_secret,SCOPES)
        creds=flow.run_local_server(port=0)
    path.write_text(creds.to_json());path.chmod(0o600)
    return creds

def gmail(creds): return build('gmail','v1',credentials=creds,cache_discovery=False)
def sheets(creds): return build('sheets','v4',credentials=creds,cache_discovery=False)
def get_sheet_rows(service,spreadsheet_id,range_name):
    return service.spreadsheets().values().get(spreadsheetId=spreadsheet_id,range=range_name).execute().get('values',[])
def update_sheet_values(service,spreadsheet_id,range_name,rows):
    return service.spreadsheets().values().update(spreadsheetId=spreadsheet_id,range=range_name,valueInputOption='RAW',body={'values':rows}).execute()
def list_messages(service,query='in:inbox newer_than:14d',max_results=100):
    return service.users().messages().list(userId='me',q=query,maxResults=max_results).execute().get('messages',[])
def get_message(service,message_id):
    return service.users().messages().get(userId='me',id=message_id,format='full').execute()
def send_message(service,raw_b64url):
    # Requires explicit operator enablement and any platform approvals.
    return service.users().messages().send(userId='me',body={'raw':raw_b64url}).execute()
