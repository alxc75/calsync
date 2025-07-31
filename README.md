<div align="center">

# CalSync
[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)]()

***Sync your Outlook/Teams calendar to Google's even when export is restricted***

</div>

## Installation

First download the code using the green `Code` button above or use `git clone`. Then install the dependencies:
```bash
pip install -r requirements.txt
playwright install
```

Now you'll need to get the credentials to modify your Google Calendar.
To do so, you will need to create a personal account on [Google's Cloud Console](https://console.cloud.google.com/)

Create a new project at the top of your screen and enable the [Calendar API](https://console.cloud.google.com/marketplace/product/google/calendar-json.googleapis.com) (it's free).

Then head to the [Credentials](https://console.cloud.google.com/apis/credentials) screen. Click the "Create credentials" button at the top and then "OAuth client ID".
Then, select `Desktop` for the app type and give it a name (the name itself doesn't matter).

A popup will appear once you click on Create. **Click the `Download JSON` button**. Then, rename that file to `credentials.json` and drop it into the `calsync` folder your previously downloaded.

At this point, you're good to go!

## Usage

To get started, open a terminal window in your `calsync` folder and run
```bash
python app.py
```
Note that you can also pass a frequency argument (day/week/month) to customize the date range to update. For example:
```bash
python app.py week
```

You will need to login in to your Outlook Calendar first, and once the app is done collecting your meetings and events, connect and authorize access to your Google account. Only calendar read and write permissions are requested.

And that's it! Now, all you have to do to update your Google Calendar is run the app again at your convenience.
