import logging
from logging.handlers import RotatingFileHandler

import requests
from bs4 import BeautifulSoup
import locale
import re

import dateparser
from datetime import datetime, timezone, timedelta

from ics import Calendar, Event
from ics.grammar.parse import ContentLine
import os

import subprocess
from dotenv import load_dotenv

#######################################################################################

locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')

## LOGGER

os.makedirs("log", exist_ok=True)

logger = logging.getLogger("scraping_logger")
logger.setLevel(logging.INFO)

log_file = "log/scraping.log"
handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=5)
handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

## REPO SETTINGS
load_dotenv()
token = os.getenv("GITHUB_TOKEN")
repo_url = f"https://{token}@github.com/LeanderWernst/combat-sports-event-scraper.git"

#######################################################################################

# TODO: Get description and location
def scrape_ufc():
    config = {
        "headers": {
            "Accept-Language": "en",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        },
        "cookies": { 
            "STYXKEY_region": "GERMANY.DE.en.Default" 
        },
        "duration": 4,
        "base_domain": "https://www.ufc.com",
        "scrape_domain": "https://www.ufc.com/events"
    }
    
    
    response = requests.get(config["scrape_domain"], headers=config["headers"], cookies=config["cookies"])

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        event_cards = soup.find_all('div', class_='c-card-event--result__info')

        events = []

        for card in event_cards:
            a_fight_detail_url = card.find('a', href=True)
            href = a_fight_detail_url['href']

            # URL
            event_url = config["base_domain"] + href

            # Name formatting
            fight_name = a_fight_detail_url.text.strip()
            if "ufc-fight-night" in href:
                event_name = f"UFC Fight Night: {fight_name}"
            else:
                ufc_number = re.search(r'ufc-(\d+)', href)
                if ufc_number:
                    event_name = f"UFC {ufc_number.group(1)}: {fight_name}"
                else: # Get Headline from detail page
                    detail_page = BeautifulSoup(requests.get(event_url, headers=config["headers"], cookies=config["cookies"]).text, 'html.parser')
                    event_headline = detail_page.find('h1').text.strip()
                    event_name = f"{event_headline}: {fight_name}"
            
            # Location
            venue = card.find('div', class_=["field field--name-taxonomy-term-title", "field--type-ds", "field--label-hidden", "field__item"]).find('h5').text.strip()
            locality = card.find('span', class_="locality")
            area = card.find('span', class_="administrative-area")
            country = card.find('span', class_="country")
            address = (", " + locality.text.strip() if locality else "") + (", " + area.text.strip() if area else "") + (", " + country.text.strip() if country else "")
            location = venue + address

            # Begin
            div_fight_dates = card.find('div', class_='c-card-event--result__date')
            event_dates = {
                "Main-Card": "data-main-card-timestamp",
                "Prelims": "data-prelims-card-timestamp"
            }

            # Parsing of dates and event creation for each date
            for section, timestamp_id in event_dates.items():
                timestamp = div_fight_dates[timestamp_id]
                parsed_begin_date = dateparser.parse(timestamp).astimezone(timezone.utc)
                event_begin_utc = parsed_begin_date.astimezone(timezone.utc).isoformat() if parsed_begin_date else None
                event_end_utc = (parsed_begin_date + timedelta(hours=config["duration"])).astimezone(timezone.utc).isoformat()

                event = {
                    "name": event_name + " - " + section,
                    "begin": event_begin_utc,
                    "end": event_end_utc,
                    "location": location,
                    # "description" ,
                    "url": event_url
                }
                events.append(event)
        events = sorted(events, key=lambda event: event["begin"], reverse=True)
        logger.info(f'Success!')
        return events

# TODO: Check events in existing ics for changes
def update_calendar(events, calendar_file, calendar_name):
    logger.info(f'Updating calendar for {calendar_name}...')

    os.makedirs('ics', exist_ok=True)
    calendar_path = os.path.join('ics', calendar_file)
    if os.path.exists(calendar_path):
        with open(calendar_path, 'r') as f:
            calendar = Calendar(f.read())
    else:
        calendar = Calendar()
        calendar.name = calendar_name
        calendar.extra.append(ContentLine(name="X-WR-CALNAME", value=calendar_name)) # for iCal


    existing_events = {event.url for event in calendar.events}

    for event_data in events:
        event_name = event_data['name']
        event_begin = datetime.fromisoformat(event_data.get('begin', None))
        event_end = datetime.fromisoformat(event_data.get('end', None))
        event_location = event_data.get("location", None)
        event_url = event_data.get("url", None)
        event_description = event_data.get("description", None)

        if event_url not in existing_events:
            event = Event()
            event.name = event_name
            event.begin = event_begin
            event.end = event_end
            event.description = event_description
            event.location = event_location
            event.url = event_url
            calendar.events.add(event)
        else:
            # TODO: detect and apply changes
            break

    with open(calendar_path, 'w') as f:
        f.writelines(calendar)
    logger.info(f'Success!')

organisations = {
    "ufc": {
        "scrape_function": scrape_ufc,
        "ical_file": "ufc_events.ics",
        "ical_name": "UFC Events"
    }
}

def git_commit_and_push():
    try:
        subprocess.run(["git", "add", "ics/*.ics"], check=True)
        subprocess.run(["git", "commit", "-m", "AUTO: update ics files"], check=True)
        subprocess.run(["git", "push", repo_url], check=True)
        logger.info("Changes successfully commited and pushed to remote.")

    except subprocess.CalledProcessError as e:
        logger.info("Error executing Git command:", e)

if __name__ == '__main__':
    logger.info("Starting scraping...")
    for org_name, org_data in organisations.items():
        logger.info(f'Scraping {org_data["ical_name"]}...')
        update_calendar(org_data["scrape_function"](), org_data["ical_file"], org_data["ical_name"])
    #git_commit_and_push()
