import asyncio
import re
import os
from playwright.async_api import async_playwright
from datetime import datetime, time, timedelta
from google_calendar import get_calendar_service, create_event, get_events, update_event
import json

async def get_meetings(freq='week'):
    """
    Fetch meetings from Outlook calendar using Playwright.

    Args:
        freq (str): Frequency of the calendar view ('day', 'week' or 'month'). Default is 'week'.

    Returns:
        list: A list of dictionaries, where each dictionary represents a meeting.
    """
    meetings_data = []
    async with async_playwright() as p:
        user_data_dir = "./user_data"
        if not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir)

        context = await p.chromium.launch_persistent_context(user_data_dir, headless=False)
        page = await context.new_page()

        print("Please log in to your Outlook account in the browser window if required...")
        await page.goto("https://outlook.office.com/calendar/view/" + freq)

        # Wait for the user to log in and the calendar to load
        await page.wait_for_selector(".calendar-SelectionStyles-resizeBoxParent", timeout=120000) # 2 minutes timeout

        meeting_elements = await page.query_selector_all(".calendar-SelectionStyles-resizeBoxParent")

        print(f"Found {len(meeting_elements)} meetings this {freq}.")

        for meeting_element in meeting_elements:
            button = await meeting_element.query_selector("div[role='button']")
            if button:
                aria_label = await button.get_attribute("aria-label")
                if aria_label:
                    # Regex to extract title, start time, end time, and date
                    match = re.match(r"([^,]+), (\d{1,2}:\d{2} [AP]M) to (\d{1,2}:\d{2} [AP]M), ([^,]+, [^,]+, \d{4})", aria_label)
                    if match:
                        title = match.group(1).strip()
                        start_time = match.group(2)
                        end_time = match.group(3)
                        date_str = match.group(4)

                        meetings_data.append({
                            "title": title,
                            "date": date_str,
                            "start_time": start_time,
                            "end_time": end_time
                        })

        await context.close()
    return meetings_data

def update_meetings(meetings_data):
    """
    Updates the Google Calendar with the provided meeting data.

    Args:
        meetings_data (list): A list of meeting dictionaries from get_meetings.
    """
    print("\nAuthenticating with Google Calendar...")
    calendar_service, user_email, user_timezone = get_calendar_service()
    if not calendar_service:
        print("Failed to authenticate with Google Calendar. Exiting.")
        return

    if not meetings_data:
        print("No meetings to sync.")
        return

    # Determine the date range of the scraped meetings
    dates = [datetime.strptime(m["date"], "%A, %B %d, %Y").date() for m in meetings_data]
    min_date = min(dates)
    max_date = max(dates)

    # Fetch existing Google Calendar events for the determined date range
    time_min = datetime.combine(min_date, time.min).isoformat() + 'Z'  # 'Z' indicates UTC
    time_max = datetime.combine(max_date, time.max).isoformat() + 'Z'

    print(f"\nFetching existing Google Calendar events from {min_date} to {max_date} to check for duplicates...")
    existing_events = get_events(calendar_service, time_min, time_max)
    # Create a dictionary mapping event titles to the full event object for easy lookup
    existing_events_dict = {event['summary']: event for event in existing_events}
    print(f"Found {len(existing_events_dict)} existing events.")

    print(f"\nProcessing {len(meetings_data)} scraped meetings...")
    for meeting in meetings_data:
        title = meeting["title"]
        start_time_str = meeting["start_time"]
        end_time_str = meeting["end_time"]
        date_str = meeting["date"]

        try:
            meeting_date = datetime.strptime(date_str, "%A, %B %d, %Y").date()
            start_time_obj = datetime.strptime(start_time_str, "%I:%M %p").time()
            end_time_obj = datetime.strptime(end_time_str, "%I:%M %p").time()
        except ValueError as e:
            print(f"Could not parse date or time for event '{title}': {e}. Skipping.")
            continue

        if title in existing_events_dict:
            existing_event = existing_events_dict[title]

            # Parse existing event's start and end times
            existing_start_dt = datetime.fromisoformat(existing_event['start'].get('dateTime').replace('Z', '+00:00'))
            existing_end_dt = datetime.fromisoformat(existing_event['end'].get('dateTime').replace('Z', '+00:00'))

            # Combine scraped date and time
            scraped_start_dt = datetime.combine(meeting_date, start_time_obj)
            scraped_end_dt = datetime.combine(meeting_date, end_time_obj)

            # Compare dates and times (ignoring timezone for a direct comparison)
            if (existing_start_dt.date() != scraped_start_dt.date() or
                existing_start_dt.time() != scraped_start_dt.time() or
                existing_end_dt.time() != scraped_end_dt.time()):

                print(f"Event '{title}' has changed. Updating in Google Calendar...")
                update_event(
                    calendar_service,
                    existing_event['id'],
                    title,
                    start_time_str,
                    end_time_str,
                    meeting_date,
                    user_email,
                    user_timezone
                )
            else:
                print(f"Event '{title}' already exists and is up to date. Skipping.")
            continue

        print(f"Creating Google Calendar event for '{title}' on {meeting_date}...")
        create_event(calendar_service, title, start_time_str, end_time_str, meeting_date, user_email, user_timezone)

async def main():
    """Main function to run the calendar sync process."""
    meetings = await get_meetings('day')
    print(json.dumps(meetings, indent=4, ensure_ascii=False))
    if meetings:
        update_meetings(meetings)
    else:
        print("No meetings found to sync.")

if __name__ == "__main__":
    print("""
######################################################
\t\tWelcome to Calsync!
######################################################
""")
    asyncio.run(main())
