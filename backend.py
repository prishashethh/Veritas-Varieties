# This is the backend for our program. Notes on each component are inside, including development timelines and iteration
# Installed packages:
# - pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2 (Google API for Gmail)
# - pip install ratelimit (to stick within the free limits for API calls on Gmail and Gemini)
# - pip install google-generativeai (for Gemini API)
# - pip install logging (for logging purposes. This was suggested as an error management mechanism)
# Both of the API calls have been limited below the paid threshold

import os
import logging
from datetime import datetime
from typing import List, Dict, Optional
import time
import json
import base64
from pathlib import Path
from dataclasses import dataclass
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from ratelimit import limits, sleep_and_retry
import google.generativeai as genai

# Configure Logging
# Displays log in email_event_processor.log, to be displayed in terminal
# Utilizes the logging library, assigns severity levels to particular failures
# Unique logger messages throughout the program, which helped us diagnose and isolate errors
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_event_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Formatting to store emails from Gmail API calls. Will be useful a bit further


@dataclass
class EmailMessage:
    """Data class to store email information."""
    message_id: str
    subject: str
    sender: str
    date: datetime
    body: str
    labels: List[str]


"""
SUPPLEMENTAL CODE - IMPLEMENTATION OF GMAIL API CLIENT - SEE AUTHENTICATE.PY FOR FIRST-TIME USE OF AUTHENTICATE(SELF) FUNCTION
class GmailAPIClient:

    # Scopes defines what permissions we need. We request modify because we mark emails once processed as read to avoid redundancy
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

    def __init__(self, credentials_path: str, token_path: str):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.credentials = None
        self.service = None

    # If token.json exists, this function just quickly communicates with Google's server
    # If it does not, we run into distinct errors that remind us to run authenticate.py on local server
    def authenticate(self) -> None:
        try:
            if Path(self.token_path).exists():
                with open(self.token_path, 'rb') as token:
                    self.credentials = pickle.load(token)

            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES
                    )
                    self.credentials = flow.run_local_server(port=9500)  # Fixed port

                with open(self.token_path, 'wb') as token:
                    pickle.dump(self.credentials, token)

            self.service = build('gmail', 'v1', credentials=self.credentials)
            logger.info("Successfully authenticated with Gmail API")

        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise


class EmailFetcher:
    # Fetches emails and extracts their content.

    def __init__(self, gmail_client: GmailAPIClient):
        self.gmail_client = gmail_client
        self.last_fetch_time = None

    @sleep_and_retry
    @limits(calls=200, period=60)  # Gmail API rate-limiting - 200 calls over a period of 60 seconds
    def fetch_recent_emails(self, max_results: int = 10) -> List[EmailMessage]:
        # Fetch recent emails with Gmail API.
        try:
            # Only opening unread emails
            query = 'label:inbox is:unread'
            if self.last_fetch_time:
                # Only opening emails delivered after the last time
                query += f' after:{int(self.last_fetch_time.timestamp())}'

            response = self.gmail_client.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            emails = []
            # Requesting Google's connection to the email, retrieving the message details
            if 'messages' in response:
                for message in response['messages']:
                    email = self._fetch_email_details(message['id'])
                    if email:
                        emails.append(email)

            self.last_fetch_time = datetime.now()
            logger.info(f"Fetched {len(emails)} emails.")
            return emails

        except Exception as e:
            logger.error(f"Error fetching recent emails: {str(e)}")
            return []

    def _fetch_email_details(self, message_id: str) -> Optional[EmailMessage]:
        # Fetch detailed email information.
        try:
            message = self.gmail_client.service.users().messages().get(
                userId='me', id=message_id, format='full'
            ).execute()

            # Sorting the retrieved email information
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
            date_str = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')

            body = self._extract_body(message['payload'])
            # Returning formatted message which we can pull the body from
            return EmailMessage(
                message_id=message_id,
                subject=subject,
                sender=sender,
                date=datetime.strptime(date_str.split(' +')[0], '%a, %d %b %Y %H:%M:%S'),
                body=body,
                labels=message.get('labelIds', [])
            )

        except Exception as e:
            logger.error(f"Error fetching email details: {str(e)}")
            return None

    def _extract_body(self, payload: Dict) -> str:
        # Extract email body content, handling MIME types.
        try:
            if 'body' in payload and payload['body'].get('data'):
                return base64.urlsafe_b64decode(payload['body']['data']).decode()

            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain' and part['body'].get('data'):
                        return base64.urlsafe_b64decode(part['body']['data']).decode()
            return "No body content found."
        except Exception as e:
            logger.error(f"Error extracting email body: {str(e)}")
            return "Error decoding body."
"""


class GeminiExtractor:
    """Uses Gemini API to extract event details."""

    # Authenticates with Gemini API key
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name="gemini-1.5-flash")

    @sleep_and_retry
    @limits(calls=50, period=60)
    # Gemini API rate-limiting - 50 calls over the course of 60 seconds. In practice, we are doubly rate-limited by the caps we have on number of emails read (for testing purposes)
    def extract_events(self, email_body: str) -> List[Dict]:
        """Extract structured events from email content."""

        # Query is designed to return a properly formatted bloc of event information for further processing into the database
        # Hallucinations or imprecisions are dealt with in app.py
        query = (
            "You are an AI assisting an events company in sorting emails to extract event data. "
            "Read the following email content and extract structured data for events. "
            "Each event should be a JSON object with the following fields: "
            "Date (yyyy-mm-dd), Name, Time (return just military time of the start of the event with ':' between hours and minutes, no other characters, ex. '19:30'), Location, Description (be concise!), and Price. "
            "If multiple events are described, return a list of JSON objects. Leave fields blank if no information is available. "
            f"Email content: {email_body}"
        )
        response_start = self.model.generate_content(query)

        # We kept this to demonstrate to you the progression of the emails from emails.txt into formatting, which is then inserted into SQL. You'll see the printed email formatting for all of them.
        print(response_start.text)

        # This command extracts the text from the response formatting
        response = response_start.text

        # We cut our the ```json...``` formatting that usually surrounds Gemini outputs
        response = response[7:-4]
        # Parse response text into a list of dictionaries
        try:
            events = json.loads(response.strip())  # Assume the model returns valid JSON-like output
            if not isinstance(events, list):
                raise ValueError("Expected a list of dictionaries from the Gemini API.")
            return events

        except Exception as e:
            logger.error(f"Error parsing response: {response.strip()} - {str(e)}")
            return []


def process_emails_from_file(file_path: str, gemini_api_key: str) -> List[Dict]:
    """
    Process emails from a file and extract event details using the Gemini API.

    Parameters:
        file_path (str): Path to the document containing emails.
        gemini_api_key (str): API key for the Gemini API.

    Returns:
        List[Dict]: A list of dictionaries representing the extracted events.
    """
    try:
        # Load the email content from the file
        with open(file_path, 'r', encoding='utf-8') as file:
            email_content = file.read()

        # Ensure email_content is a string before splitting
        if isinstance(email_content, list):
            raise TypeError("Expected email content to be a string, but got a list.")

        # Split the emails based on the separator
        emails = email_content.split(
            "***** SEPARATION *****") if isinstance(email_content, str) else email_content

        # Limit to processing the first 6 emails
        emails = emails[:12] if isinstance(emails, list) else [emails]

        gemini_extractor = GeminiExtractor(api_key=gemini_api_key)

        all_events = []
        batch_size = 3  # Process three emails per query
        logger.info(f"Processing {len(emails)} emails in batches of {batch_size}...")

        # Process emails in batches
        for i in range(0, len(emails), batch_size):
            batch = emails[i:i + batch_size]
            combined_batch_text = "\n\n".join(batch)
            logger.info(f"Processing batch {i // batch_size + 1} with {len(batch)} emails...")

            try:
                events = gemini_extractor.extract_events(combined_batch_text)
                all_events.extend(events)  # Add extracted events to the list
                logger.info(f"Events extracted: {events}")
            except Exception as e:
                logger.error(f"Error processing batch {i // batch_size + 1}: {str(e)}")
                continue

        logger.info(f"Total events processed: {len(all_events)}")
        return all_events

    except Exception as e:
        logger.error(f"Error reading or processing emails from file: {str(e)}")
        return []
