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

Then head to the [Credentials](https://console.cloud.google.com/apis/credentials) screen. Click the "Create credentials" button at the top and then "OAuth client ID". You will most likely need to configure the OAuth screen first. It will ask for the app name and your email address.
Then, select `Desktop` for the app type and give it a name (the name itself doesn't matter).

A popup will appear once you click on Create. **Click the `Download JSON` button**. Then, rename that file to `credentials.json` and drop it into the `calsync` folder your previously downloaded.

At this point, you're good to go!

## Usage

There are two ways to run CalSync. Directly as a script (with terminal output) or as a MacOS App that you can put in your dock, just like a real app. So if you don't care about seeing the detail of which event was skipped or you just want a single button/app to click, choose the latter.

Below are installation and usage instructions.

### Script Usage

To get started, open a terminal window in your `calsync` folder and run

```bash
python app.py
```

Note that you can also pass a frequency argument (day/week/month) to customize the date range to update. Defualt For example:

```bash
python app.py week
```

First, you'll be asked to enter your Google Calendar address. It's used so that the event is skipped if you're already a participant on this address too. Otherwise you would have a duplicate in your Google Calendar.

You will need to login in to your Outlook Calendar, and once the app is done collecting your meetings and events, connect and authorize access to your Google account. Only calendar read and write permissions are requested.

And that's it! Now, all you have to do to update your Google Calendar is run the app again at your convenience.

You can also add keywords you would like to skip in the automatically generated `user.json`. For example, if you wanted to skip all meetings containing the text "daily" or "weekly", you have something like this:

```json
{
    "user_email": "youremail@example.com",
    "frequency": "day",
    "ignore_list": ["daily", "weekly"]
}
```

### App Config

To create the app, run the `create_app.sh` script in your terminal with this:

```bash
bash create_app.sh
```

The script will install its self-contained dependencies and ask you a few questions to configure the settings below.
Once everything is done, a Finder window with the app will appear. You can then drag the app to your Dock.

When you run CalSync as an app, the user config is located at `~/Library/Application Support/CalSync/user.json`. This file is created automatically when you run the `create_app.sh` script. There is a script to edit the config (see below).

Configuration settings include:

- `user_email`: Your Google Calendar email address (used to avoid duplicates)
- `frequency`: Calendar view to sync ('day', 'week', or 'month')
- `ignore_list`: List of keywords in event titles that should be skipped during sync

You can still override settings via command line arguments: `--frequency` or `--email` via the bash script serving as an entrypoint in the CalSync.app package.
However, to update the settings above, I recommend running `edit_config.sh` instead. It's an interactive script and will prevent syntax errors. You can also use it to display your current configuration.

```bash
bash edit_config.sh
```
