import logging
from logging.handlers import RotatingFileHandler

import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import time
import locale
import re
import json
from collections import defaultdict

import dateparser
from datetime import datetime, timezone, timedelta

from ics import Calendar, Event
from ics.grammar.parse import ContentLine
import os

import subprocess
import glob
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
repo_url = f"https://{token}@github.com/LeanderWernst/combat-sports-events.git"

## SELENIUM WEBDRIVER
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

#######################################################################################

CATEGORY = {
    "MMA": "mma",
    "MUAY_THAI": "muaythai",
    "K1": "k1",
    "KICKBOXING": "kickboxing",
    "GRAPPLING": "grappling",
    "BOXING": "boxing",
    "BAREKNUCKLE": "bareknuckle",
    "BJJ": "bjj"
}

def scrape_glory():
    config = {
        "headers": {
            "Accept-Language": "en",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        },
        "duration": 3,
        "base_domain": "https://glorykickboxing.com",
        "scrape_domain": "https://glorykickboxing.com/events"
    }

    events = []

    try:       
        driver.get(config["scrape_domain"])
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href^="/events/"]'))
        )
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        #event_cards = soup.find_all('div', class_=['card', 'gold', 'event-card'])
        a_event_links = soup.find_all('a', href=re.compile(r'^/events/'))
        event_links = { link['href'].split('#')[0] for link in a_event_links }

        for link in event_links:
            driver.get(config["base_domain"] + link)
            element = WebDriverWait(driver, 10).until(
                lambda d: d.find_elements(By.CSS_SELECTOR, 'div[class="info"]') or 
                          d.find_elements(By.CSS_SELECTOR, 'div[class="bar longAgo info-bar"]')
            )
            has_info_div = element[0].get_attribute('class') == "info" if element else False

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            event_title = soup.find('title').text
            # event_name = soup.find('meta', property="og:title")["content"]
            event_description = soup.find('meta', property="og:description")["content"]
            if has_info_div:
                location = soup.find('span', class_="location-top").text.strip()
                div_info = soup.find('div', class_="info")
                start_main = div_info.find('span').text.strip()
                date_split = re.split(r'(\d{4})', start_main)
                date = date_split[0] + " " + date_split[1]
                start_main_utc = dateparser.parse(start_main, settings={'TIMEZONE': 'CET', 'TO_TIMEZONE': 'UTC'}).isoformat()
                start_prelims = div_info.find('span', string=re.compile(r'Prelims')).text.strip().replace('Prelims', '') if div_info.find('span', string=re.compile(r'Prelims')) else None
                start_prelims_utc = dateparser.parse(date + start_prelims, settings={'TIMEZONE': 'CET', 'TO_TIMEZONE': 'UTC'}).isoformat() if start_prelims else None
                end_main_utc = (dateparser.parse(start_main, settings={'TIMEZONE': 'CET', 'TO_TIMEZONE': 'UTC'}) + timedelta(hours=config["duration"])).isoformat()
            else:
                location = soup.find('span', class_="location-large").text.strip()
                date = soup.find('div', class_="large live clock").find('label').text.strip()
                h3s_main_card = soup.find_all('h3')
                start_main = None
                for h3 in h3s_main_card:
                    if 'Main' in h3.text.strip():
                        main_text = h3.text.strip()
                    elif 'Prelims' in h3.text.strip():
                        prelims_text = h3.text.strip()
                start_main = main_text.replace('Main cardLive at ', '')
                start_main_utc = dateparser.parse(date + " " + start_main, settings={'TIMEZONE': 'CET', 'TO_TIMEZONE': 'UTC'}).isoformat()
                start_prelims = prelims_text.replace('PrelimsLive at ', '') if prelims_text else None
                start_prelims_utc = dateparser.parse(date + " " + start_prelims, settings={'TIMEZONE': 'CET', 'TO_TIMEZONE': 'UTC'}).isoformat()
                end_main_utc = (dateparser.parse(date + " " + start_main, settings={'TIMEZONE': 'CET', 'TO_TIMEZONE': 'UTC'}) + timedelta(hours=config["duration"])).isoformat()

            event =  {
                "url": config["base_domain"] + link,
                "organization": "glory",
                "title": event_title,
                "date": start_main_utc,
                "description": event_description,
                "broadcast": ["triller_tv"],
                "venue": location,
                "category": "mma",
                "cards": {
                    "main_card": {
                            "start": start_main_utc,
                            "end": end_main_utc
                    },
                    "prelims": {
                        "start": start_prelims_utc if start_prelims else None,
                        "end": start_main_utc if start_prelims else None
                    }
                },
                "last_updated": datetime.now(timezone.utc).isoformat() + "Z",
            }
            events.append(event)
        events = sorted(events, key=lambda event: event["date"], reverse=True)
        save_events(events, 'glory.json')
        logger.info(f'Success!')
        return events

    finally:
        driver.quit()

""" def scrape_one_championship():
    config = {
        "headers": {
            "Accept-Language": "en",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        },
        "duration": 3,
        "base_domain": "https://www.onefc.com",
        "scrape_domain": "https://www.onefc.com/events/"
    }

    events = []

    try:
        response = requests.get(config["scrape_domain"], headers=config["headers"])
        soup = BeautifulSoup(response.content, 'html.parser')
        
        event_cards = soup.find_all('div', class_='simple-post-card is-event is-image-zoom-area')

        for card in event_cards:
            event_link = card.find('a', class_='title')['href']
            event_url = event_link

            event_title = card.find('a', class_='title')['title']
            event_datetime = card.find('div', class_='datetime')['data-timestamp']
            location_div = card.find('div', class_='location')
            event_venue = location_div.text.strip() if location_div else "n/a"

            start_main_utc = datetime.fromtimestamp(int(event_datetime), tz=timezone.utc).isoformat()
            end_main_utc = (datetime.fromtimestamp(int(event_datetime), tz=timezone.utc) + timedelta(hours=config["duration"])).isoformat()

            event = {
                "url": event_url,
                "organization": "one_championship",
                "title": event_title,
                "date": start_main_utc,
                "description": f"ONE Championship event: {event_title}",
                "broadcast": ["onefc", "youtube"],
                "venue": event_venue,
                "category": ["mma", "kickboxing", "grappling", "muay thai"],
                "cards": {
                    "main_card": {
                        "start": start_main_utc,
                        "end": end_main_utc
                    },
                    "prelims": {
                        "start": None,
                        "end": None
                    }
                },
                "last_updated": datetime.now(timezone.utc).isoformat() + "Z",
            }
            events.append(event)

        events = sorted(events, key=lambda event: event["date"], reverse=True)
        save_events(events, 'one_championship.json')
        return events

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return [] """

def write_events_to_json(events, filename):
    """
    Saves events in /json/{year} and updates existing.
    
    Args:
        events (list): Liste of events
        filename (str): Filename without path
    """
    if not events:
        logger.info("No events found for saving.")
        return
    
    event_year = datetime.fromisoformat(events[0]["date"]).year
    dir_path = f"./json/{event_year}"
    file_path = os.path.join(dir_path, filename)
    
    os.makedirs(dir_path, exist_ok=True)
    
    existing_events = []
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            existing_events = json.load(file)

    events_dict = {event["url"]: event for event in existing_events}

    for new_event in events:
        url = new_event["url"]
        if url in events_dict:
            existing_event = events_dict[url]
            updated = False
            for key, value in new_event.items():
                if key in existing_event and existing_event[key] != value:
                    existing_event[key] = value
                    updated = True
            if updated:
                logger.info(f"Event updated: {url}")
        else:
            events_dict[url] = new_event
            logger.info(f"Added event: {url}")

    updated_events = list(events_dict.values())

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(updated_events, file, indent=2, ensure_ascii=False)

def fetch_and_convert_one_ics_to_json():
    response = requests.get(organisations["one"]["ical_file"])
    response.raise_for_status()

    calendar = Calendar(response.text)

    broadcast = ["onefc", "youtube"]
    category = ["mma", "kickboxing", "grappling", "muay thai"]

    events = []

    for event in calendar.events:
        event_json = {
            "url": event.url if event.url else "n/a",
            "organization": "one_championship",
            "title": event.name,
            "date": event.begin.isoformat(),
            "description": event.description.split("\n\n")[1:-1] if event.description else [],
            "broadcast": broadcast,
            "venue": event.location if event.location else "n/a",
            "category": category,
            "cards": {
                "main_card": {
                    "start": event.begin.isoformat(),
                    "end": event.end.isoformat() if event.end else None
                },
                "prelims": {
                    "start": None,
                    "end": None
                }
            },
            "last_updated": datetime.now(timezone.utc).isoformat() + "Z"
        }

        events.append(event_json)
    events = sorted(events, key=lambda event: event["date"], reverse=True)
    save_events(events, 'one_championship.json')
    logger.info(f'Success!')
    return events


def split_events_by_year(events):
    """
    Splits a list of events by year and returns a dictionary, where the key is the year and the value is a list of events.
    """
    events_by_year = defaultdict(list)

    for event in events:
        event_date = datetime.fromisoformat(event["date"])
        event_year = event_date.year
        events_by_year[event_year].append(event)
    
    return events_by_year

def save_events(events, filename):
    events_by_year = split_events_by_year(events)
    for year, events_list in events_by_year.items():
        write_events_to_json(events_list, filename)



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
            main_card_begin = None
            main_card_end = None
            prelims_begin = None
            prelims_end = None
            for section, timestamp_id in event_dates.items():
                timestamp = div_fight_dates[timestamp_id]
                parsed_begin_date = dateparser.parse(timestamp).astimezone(timezone.utc)
                event_begin_utc = parsed_begin_date.astimezone(timezone.utc).isoformat() if parsed_begin_date else None
                
                if section == "Main-Card":
                    main_card_end = (parsed_begin_date + timedelta(hours=config["duration"])).astimezone(timezone.utc).isoformat()
                    main_card_begin = parsed_begin_date.isoformat()
                elif section == "Prelims" and main_card_begin:
                    prelims_end = main_card_begin
                    prelims_begin = parsed_begin_date.isoformat()

            event =  {
                "url": event_url,
                "organization": "ufc",
                "title": event_name,
                "date": event_begin_utc,
                "description": None,
                "broadcast": ["triller_tv"],
                "venue": location,
                "category": "mma",
                "cards": {
                    "main_card": {
                            "start": main_card_begin,
                            "end": main_card_end
                    },
                    "prelims": {
                        "start": prelims_begin if prelims_begin else None,
                        "end": prelims_end if prelims_end else None
                    }
                },
                "last_updated": datetime.now(timezone.utc).isoformat() + "Z",
            }
            events.append(event)
        events = sorted(events, key=lambda event: event["date"], reverse=True)
        save_events(events, 'ufc.json')
        logger.info(f'Success!')
        return events

def get_custom_ical_property(event, property_name):
    for line in event.extra:
        if line.name == property_name:
            return line.value
    return None

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

    existing_events = {event.url: event for event in calendar.events}

    for event_data in events:
        event_url = event_data.get("url", None)
        event_name = event_data['title']
        card_dict = {'prelims': "Preliminaries",'main_card': "Main Card"}
        for card, card_name in card_dict.items():
            event_url_card_specific = event_url + "#" + card
            event_description = event_data.get("description", None)
            event_location = event_data.get("venue", None)

            # url in json is valid for prelims and main, so we need to add url id present in events
            if event_url_card_specific not in existing_events:
                # Add new events
                
                if not event_data['cards'][card]['start']:
                        continue

                event = Event()
                event.extra.append(ContentLine(name="X-FIGHTCARD", value=card))
                event.name = event_name + " - " + card_name
                event.begin = datetime.fromisoformat(event_data['cards'][card]['start'])
                event.end = datetime.fromisoformat(event_data['cards'][card]['end'])
                event.description = event_description
                event.location = event_location
                event.last_modified = datetime.now()
                event.url = event_url_card_specific # for unique urls in events
                calendar.events.add(event)

            else:
                # Update existing event if not in past
                existing_event = existing_events[event_url_card_specific]
                if not existing_event.begin < datetime.now(timezone.utc):
                    # name is not equal, since events have additional card info
                    if event_name not in existing_event.name:
                        existing_event.name = event_name + " - " + card_dict[get_custom_ical_property(existing_event, 'X-FIGHTCARD')]
                        existing_event.last_modified = datetime.now(timezone.utc)
                    for property, value in {
                        "begin": datetime.fromisoformat(event_data['cards'][get_custom_ical_property(existing_event, 'X-FIGHTCARD')]['start']),
                        "end": datetime.fromisoformat(event_data['cards'][get_custom_ical_property(existing_event, 'X-FIGHTCARD')]['end']),
                        "description": event_description,
                        "location": event_location
                    }.items():
                        if getattr(existing_event, property) != value:
                            setattr(existing_event, property, value)
                            existing_event.last_modified = datetime.now(timezone.utc)

    with open(calendar_path, 'w') as f:
        f.writelines(calendar)
    logger.info(f'Success!')

organisations = {
    "ufc": {
        "scrape_function": scrape_ufc,
        "ical_file": "ufc_events.ics",
        "ical_name": "UFC Events"
    },
    "glory": {
        "scrape_function": scrape_glory,
        "ical_file": "glory_events.ics",
        "ical_name": "Glory Events"
    },
    "one": {
        "scrape_function": fetch_and_convert_one_ics_to_json,
        "ical_file": "https://calendar.onefc.com/ONE-Championship-events.ics",
        "ical_name": "One Champtionship"
    }
}

def git_pull():
    try:
        subprocess.run(["git", "pull", "--no-edit"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error("Error during git pull: Check for merge conflicts.")
        raise

def git_add_files(pattern):
    files = glob.glob(pattern, recursive=True)
    if files:
        subprocess.run(["git", "add"] + files, check=True)

def git_commit_and_push():
    try:
        # Check if there are changes
        result = subprocess.run(["git", "status", "--porcelain"], check=True, stdout=subprocess.PIPE, text=True)
        if not result.stdout.strip():
            logger.info("No changes to commit.")
            return
        
        # Commit and push changes
        subprocess.run(["git", "commit", "-m", "AUTO: update ics and json files"], check=True)
        subprocess.run(["git", "push", repo_url], check=True)
        logger.info("Changes successfully committed and pushed to remote.")
    except subprocess.CalledProcessError as e:
        logger.error("Error executing Git command:", e)
        raise

def debug():
    fetch_and_convert_one_ics_to_json()

if __name__ == '__main__':
    git_pull()
    logger.info("Starting scraping...")
    for org_name, org_data in organisations.items():
        try:
            logger.info(f'Scraping {org_data["ical_name"]}...')
            update_calendar(org_data["scrape_function"](), org_data["ical_file"], org_data["ical_name"])
        except Exception as e:
            logger.error(f"Error updating calendar for {org_name}: {e}")
    git_add_files("ics/**/*.ics")
    git_add_files("json/**/*.json")
    git_commit_and_push()
    # debug()