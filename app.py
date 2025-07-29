import asyncio
import re
import os
from playwright.async_api import async_playwright

async def get_meetings(freq='week'):
    """
    Fetch meetings from Outlook calendar using Playwright.

    Args:
        freq (str): Frequency of the calendar view ('day', 'week' or 'month'). Default is 'week'.

    Returns:
        None
    """

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
                    # Regex to extract title, start time, and end time
                    match = re.match(r"([^,]+), (\d{1,2}:\d{2} [AP]M) to (\d{1,2}:\d{2} [AP]M)", aria_label)
                    if match:
                        title = match.group(1).strip()
                        start_time = match.group(2)
                        end_time = match.group(3)

                        print("\n--- Meeting ---")
                        print(f"Title: {title}")
                        print(f"Start Time: {start_time}")
                        print(f"End Time: {end_time}")

        await context.close()

if __name__ == "__main__":
    asyncio.run(get_meetings('day'))
