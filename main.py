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
repo_url = f"https://{token}@github.com/LeanderWernst/combat-sports-events.git"

## SELENIUM WEBDRIVER
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

#######################################################################################

# TODO: Use selenium
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
        event_links = { link['href'] for link in a_event_links }
        print(event_links)

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
            print(link, soup)
            start_prelims_utc, start_main_utc, location = "", "", ""
            if has_info_div:
                location = soup.find('span', class_="location-top").text.strip()
                div_info = soup.find('div', class_="info")
                start_main = div_info.find('span').text.strip()
                date_split = re.split(r'(\d{4})', start_main)
                date = date_split[0] + " " + date_split[1]
                start_main_utc = dateparser.parse(start_main).astimezone(timezone.utc).isoformat()
                start_prelims = div_info.find('span', string=re.compile(r'Prelims')).text.strip().replace('Prelims', '') if div_info.find('span', string=re.compile(r'Prelims')) else None
                start_prelims_utc = dateparser.parse(date + start_prelims).astimezone(timezone.utc).isoformat() if start_prelims else None
                end_main_utc = (dateparser.parse(start_main).astimezone(timezone.utc) + timedelta(hours=config["duration"])).isoformat()
            else:
                print(link)
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
                start_main_utc = dateparser.parse(date + " " + start_main).astimezone(timezone.utc).isoformat()
                start_prelims = prelims_text.replace('PrelimsLive at ', '') if prelims_text else None
                start_prelims_utc = dateparser.parse(date + " " + start_prelims).astimezone(timezone.utc).isoformat()
                end_main_utc = (dateparser.parse(start_main).astimezone(timezone.utc) + timedelta(hours=config["duration"])).isoformat()

                if start_prelims:
                    prelims = {
                            "name": event_title,
                            "begin": start_prelims_utc,
                            "end": start_main_utc,
                            "location": location,
                            "description": event_description ,
                            "url": config["base_domain"] + link
                    }
                    events.append(prelims)
                main = {
                        "name": event_title,
                        "begin": start_main_utc,
                        "end": end_main_utc,
                        "location": location,
                        "description": event_description ,
                        "url": config["base_domain"] + link
                }
                events.append(main)
        events = sorted(events, key=lambda event: event["begin"], reverse=True)
        logger.info(f'Success!')
        return events

    finally:
        driver.quit()




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
            for section, timestamp_id in event_dates.items():
                timestamp = div_fight_dates[timestamp_id]
                parsed_begin_date = dateparser.parse(timestamp).astimezone(timezone.utc)
                event_begin_utc = parsed_begin_date.astimezone(timezone.utc).isoformat() if parsed_begin_date else None
                
                if section == "Main-Card":
                    event_end_utc = (parsed_begin_date + timedelta(hours=config["duration"])).astimezone(timezone.utc).isoformat()
                    main_card_begin = parsed_begin_date
                elif section == "Prelims" and main_card_begin:
                    event_end_utc = main_card_begin.isoformat()

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
    },
    "glory": {
        "scrape_function": scrape_glory,
        "ical_file": "glory_events.ics",
        "ical_name": "Glory Events"
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
    git_commit_and_push()