import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.events", "https://www.googleapis.com/auth/userinfo.email", "openid", "https://www.googleapis.com/auth/calendar.readonly"]


def get_calendar_service():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        # Get user's email and timezone
        user_info_service = build('oauth2', 'v2', credentials=creds)
        user_info = user_info_service.userinfo().get().execute()
        user_email = user_info.get('email')

        calendar_info = service.calendars().get(calendarId='primary').execute()
        user_timezone = calendar_info.get('timeZone')

        if not user_email or not user_timezone:
            print("Could not retrieve user email or timezone. Exiting.")
            return None, None, None

        return service, user_email, user_timezone
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None, None, None

def get_events(service, time_min, time_max):
    """Fetch events from Google Calendar within a given time range."""
    try:
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return events_result.get('items', [])
    except HttpError as error:
        print(f"An error occurred while fetching events: {error}")
        return []

def update_event(service, event_id, summary, start_time_str, end_time_str, date, user_email, time_zone):
    """Updates an existing event in the Google Calendar."""

    start_datetime = datetime.datetime.combine(date, datetime.datetime.strptime(start_time_str, "%I:%M %p").time())
    end_datetime = datetime.datetime.combine(date, datetime.datetime.strptime(end_time_str, "%I:%M %p").time())

    event_body = {
        'summary': summary,
        'start': {
            'dateTime': start_datetime.isoformat(),
            'timeZone': time_zone,
        },
        'end': {
            'dateTime': end_datetime.isoformat(),
            'timeZone': time_zone,
        },
        'attendees': [
            {'email': user_email},
        ],
    }
    try:
        updated_event = service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event_body,
            sendUpdates='all'
        ).execute()
        print(f"Event updated: {updated_event.get('htmlLink')}")
    except HttpError as error:
        print(f"An error occurred while updating event '{summary}': {error}")


def delete_event(service, event_id):
    """Deletes an event from the Google Calendar."""
    try:
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        print(f"Event with ID {event_id} deleted.")
    except HttpError as error:
        print(f"An error occurred while deleting event ID {event_id}: {error}")


def create_event(service, summary, start_time_str, end_time_str, date, user_email, time_zone):
    """Creates an event in the Google Calendar."""

    start_datetime = datetime.datetime.combine(date, datetime.datetime.strptime(start_time_str, "%I:%M %p").time())
    end_datetime = datetime.datetime.combine(date, datetime.datetime.strptime(end_time_str, "%I:%M %p").time())

    event = {
        'summary': summary,
        'start': {
            'dateTime': start_datetime.isoformat(),
            'timeZone': time_zone,
        },
        'end': {
            'dateTime': end_datetime.isoformat(),
            'timeZone': time_zone,
        },
        'attendees': [
            {'email': user_email},
        ],
    }

    event = service.events().insert(calendarId='primary', body=event, sendUpdates='all').execute()
    print(f"Event created: {event.get('htmlLink')}")
