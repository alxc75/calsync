import asyncio
import re
import os
import argparse
from playwright.async_api import async_playwright
from playwright._impl._errors import TargetClosedError
from datetime import datetime, time, timedelta
from google_calendar import get_calendar_service, create_event, get_events, update_event, delete_event
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
    try:
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
                try:
                    button = await meeting_element.query_selector("div[role='button']")
                    if not button:
                        continue

                    # 1. Click event to open preview
                    await button.click()

                    # 2. Click "View event" to open full details
                    view_event_selector = "button[aria-label='View event']"
                    await page.wait_for_selector(view_event_selector, timeout=5000)
                    view_event_button = await page.query_selector(view_event_selector)
                    if view_event_button:
                        await view_event_button.click()

                    # 3. Scrape description from full details view
                    description_selector = "div[id^='UniqueMessageBody_']"
                    await page.wait_for_selector(description_selector, timeout=5000)
                    description_element = await page.query_selector(description_selector)
                    description = await description_element.inner_html() if description_element else ""

                    # Clean the HTML description
                    if description:
                        # 1. Replace all div and p tags (and their closing tags) with a single line break.
                        # This handles complex tags like <div class="..."> or <p style="...">
                        description = re.sub(r'</?p.*?>', '<br>', description, flags=re.IGNORECASE)
                        description = re.sub(r'</?div.*?>', '<br>', description, flags=re.IGNORECASE)

                        # 2. Collapse any instance of multiple (two or more) line breaks into just one.
                        description = re.sub(r'(<br\s*/?>\s*){2,}', '<br>', description)

                        # 3. Remove any leading or trailing line breaks that might be left.
                        description = description.strip().strip('<br>').strip()

                    # Scrape original event details from the button's aria-label
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
                                "end_time": end_time,
                                "description": description
                            })

                except Exception as e:
                    print(f"Could not process an event, skipping. Error: {e}")
                finally:
                    # 4. Close the details view to go back
                    close_button = await page.query_selector("button[aria-label='Close']")
                    if close_button:
                        await close_button.click()
                        # Add a small delay to ensure the modal is closed before the next iteration
                        await page.wait_for_timeout(500)


            await context.close()
        return meetings_data
    except TargetClosedError:
        print("\nWindow closed. Outlook sync process interrupted.")
        return [] # Return an empty list to exit cleanly

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

    # Load ignore list
    ignore_list = []
    if os.path.exists("ignore.txt"):
        with open("ignore.txt", "r") as f:
            ignore_list = [line.strip() for line in f if line.strip()]
        if ignore_list:
            print(f"\nLoaded {len(ignore_list)} strings from ignore.txt. Meetings containing these strings will be ignored.")

    # Determine the date range of the scraped meetings
    try:
        dates = [datetime.strptime(m["date"], "%A, %B %d, %Y").date() for m in meetings_data]
        min_date = min(dates)
        max_date = max(dates)
    except (ValueError, KeyError) as e:
        print(f"Could not determine date range from meetings data: {e}. Cannot fetch existing events.")
        # Decide if you want to exit or continue without checking for duplicates
        return


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

        # Check if the meeting title contains any string from the ignore list
        if any(ignore_str in title for ignore_str in ignore_list):
            print(f"Event '{title}' contains an ignored keyword. Skipping.")
            continue

        # Handle cancelled events
        cancelled_prefixes = ["Annulé : ", "Cancelled: "]
        original_title = title
        is_cancelled = False
        for prefix in cancelled_prefixes:
            if title.startswith(prefix):
                original_title = title.replace(prefix, "").strip()
                is_cancelled = True
                break

        if is_cancelled:
            if original_title in existing_events_dict:
                event_to_delete = existing_events_dict[original_title]
                print(f"Event '{original_title}' was cancelled. Deleting from Google Calendar...")
                delete_event(calendar_service, event_to_delete['id'])
            else:
                print(f"Cancelled event '{original_title}' not found in Google Calendar. Skipping.")
            continue

        start_time_str = meeting["start_time"]
        end_time_str = meeting["end_time"]
        date_str = meeting["date"]
        description = meeting.get("description", "") # Get description, default to empty string

        try:
            meeting_date = datetime.strptime(date_str, "%A, %B %d, %Y").date()
            start_time_obj = datetime.strptime(start_time_str, "%I:%M %p").time()
            end_time_obj = datetime.strptime(end_time_str, "%I:%M %p").time()
        except ValueError as e:
            print(f"Could not parse date or time for event '{title}': {e}. Skipping.")
            continue

        # Check if the meeting is in the past and skip if it is
        meeting_start_datetime = datetime.combine(meeting_date, start_time_obj)
        if meeting_start_datetime < datetime.now():
            print(f"Event '{title}' is in the past. Skipping.")
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
                existing_end_dt.time() != scraped_end_dt.time() or
                existing_event.get('description', '') != description):

                print(f"Event '{title}' has changed. Updating in Google Calendar...")
                update_event(
                    calendar_service,
                    existing_event['id'],
                    title,
                    start_time_str,
                    end_time_str,
                    meeting_date,
                    user_email,
                    user_timezone,
                    description
                )
            else:
                print(f"Event '{title}' already exists and is up to date. Skipping.")
            continue

        # If the event is not cancelled and does not exist, create it.
        print(f"Creating Google Calendar event for '{title}' on {meeting_date}...")
        create_event(calendar_service, title, start_time_str, end_time_str, meeting_date, user_email, user_timezone, description)

async def main():
    """Main function to run the calendar sync process."""
    parser = argparse.ArgumentParser(description="Sync your Outlook calendar to Google Calendar.")
    parser.add_argument('frequency', type=str, nargs='?', default='week', choices=['day', 'week', 'month'],
                        help="The calendar view to sync: 'day', 'week', or 'month'. Defaults to 'week'.")
    args = parser.parse_args()

    meetings = await get_meetings(args.frequency)
    # print(json.dumps(meetings, indent=4, ensure_ascii=False))
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
