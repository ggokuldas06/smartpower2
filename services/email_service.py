from datetime import datetime
import os
from datetime import datetime
from services.celery_module import celery_service
import base64
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import base64
from email.mime.text import MIMEText
 
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

@celery_service.task
def send_html_email(body, email, subject, sender):
   # app = create_celery_app()
   # with app.app_context():
      
       creds = None
       # The file token.json stores the user's access and refresh tokens, and is
       # created automatically when the authorization flow completes for the first
       # time.
       if os.path.exists('token.json'):
           creds = Credentials.from_authorized_user_file('token.json', SCOPES)
       # If there are no (valid) credentials available, let the user log in.
       if not creds or not creds.valid:
           if creds and creds.expired and creds.refresh_token:
               creds.refresh(Request())
           else:
               flow = InstalledAppFlow.from_client_secrets_file(
                   'credentials.json', SCOPES)
               creds = flow.run_local_server(port=0)
           # Save the credentials for the next run
           with open('token.json', 'w') as token:
               token.write(creds.to_json())
       # http_auth = creds.authorize(httplib2shim.Http())
       service = build('gmail', 'v1', credentials=creds)
 
       sender = sender
       to = email
       message_Text = body
       msg = create_message(sender,to,subject,message_Text)
       send_message(service,"me",msg)
 
def send_message(service, user_id, message):
   """Send an email message.
   Args:
   service: Authorized Gmail API service instance.
   user_id: User's email address. The special value "me"
   can be used to indicate the authenticated user.
   message: Message to be sent.
   Returns:
   Sent Message.
   """
   try:
       message = (service.users().messages().send(userId=user_id, body=message)
               .execute())
       print ('Message Id: %s' % message['id'])
       return message
   except Exception as error:
       print ('An error occurred: %s' % error)
 
 
def create_message(sender, to, subject, message_text):
 """Create a message for an email.
 Args:
   sender: Email address of the sender.
   to: Email address of the receiver.
   subject: The subject of the email message.
   message_text: The text of the email message.
 Returns:
   An object containing a base64url encoded email object.
 """
 message = MIMEText(message_text,"html")
 message['to'] = to
 message['from'] = sender
 message['subject'] = subject
 b64_bytes = base64.urlsafe_b64encode(message.as_bytes())
 b64_string = b64_bytes.decode()
 return {'raw': b64_string}