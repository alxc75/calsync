import asyncio
import re
import os
from playwright.async_api import async_playwright
from datetime import datetime
from google_calendar import get_calendar_service, create_event
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
    calendar_service, user_email = get_calendar_service()
    if not calendar_service:
        print("Failed to authenticate with Google Calendar. Exiting.")
        return

    print(f"\nFound {len(meetings_data)} meetings to sync.")
    for meeting in meetings_data:
        title = meeting["title"]
        start_time = meeting["start_time"]
        end_time = meeting["end_time"]
        date_str = meeting["date"]

        try:
            # The date format from outlook is like 'Wednesday, July 30, 2025'
            meeting_date = datetime.strptime(date_str, "%A, %B %d, %Y").date()
        except ValueError:
            print(f"Could not parse date: {date_str}. Skipping event '{title}'.")
            continue

        print(f"Creating Google Calendar event for '{title}' on {meeting_date}...")
        create_event(calendar_service, title, start_time, end_time, meeting_date, user_email)

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
