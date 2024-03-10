import codecs
import csv
import datetime as dt
import html
import os
import random
import re
import typing
from datetime import date, datetime
from http.cookiejar import CookieJar
from pathlib import Path
from time import sleep
from urllib.request import HTTPCookieProcessor, Request, build_opener

import requests
from bs4 import BeautifulSoup

import importer_globals as G
from SeleniumLoader import SeleniumLoader

MAX_PARSE_TRIES = 3
EARLIEST_DATE = date(2018, 10, 25)
EARLIEST_DATE = date.today()

# Event columns in the correct order for importing.
# UNDERSTAND THIS BEFORE CHANGING THE ORDER.
CSV_COLUMNS_ORDERED = (
    "event_name",
    "venue_name",
    "organizer_name",
    "start_date",
    "start_time",
    "end_date",
    "end_time",
    "all_day_event",
    "categories",
    "event_cost",
    "event_phone",
    "event_website",
    "show_map_link",
    "show_map",
    "event_description",
    "external_image_url",
    "event_tags",
    "relevant",
    "start_timestamp",
)

CSV_COLUMNS = {
    "event_name": "Event Name",
    "venue_name": "Event Venue Name",
    "organizer_name": "Organizer Name",
    "start_date": "Event Start Date",
    "start_time": "Event Start Time",
    "end_date": "Event End Date",
    "end_time": "Event End Time",
    "all_day_event": "All Day Event",
    "categories": "Event Category",
    "event_cost": "Event Cost",
    "event_phone": "Event Phone",
    "event_website": "Event Website",
    "show_map_link": "Event Show Map Link",
    "show_map": "Event Show Map",
    "event_description": "Event Description",
    "external_image_url": "external_image_url",
    "event_tags": "Event Tags",
    "relevant": "Relevant",
    "start_timestamp": "Start Timestamp",
}


def is_in_new_york(lat, lon):
    """
    Returns whether a lat/lon point is in New York (except Staten Island)
    :param lat:
    :param lon:
    :return:
    """
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
    response = requests.get(url).json()

    if "address" in response:
        if "city" in response["address"]:
            if response["address"]["city"] == "City of New York":
                if "suburb" in response["address"]:
                    if response["address"]["suburb"] != "Staten Island":
                        return True
    return False


def parse_file_to_soup(file_path):
    """Parse a URL and return the parsed DOM object"""
    page = Request.urlopen("file:///{0}".format(file_path))
    soup = BeautifulSoup(page, "html.parser")
    return soup


def get_full_image_path(folder, image_file_name):
    """Return the full path to a downloaded image file given the folder and original file name
    :param folder: Destination folder
    :param image_file_name: File name from website
    :return: Full path to downloaded image file
    """
    full_image_path = f"../Images/{folder}/{folder}_{image_file_name}"
    return full_image_path


def sanitize_filename(filename: str) -> str:
    # Define the list of illegal characters in Windows filenames.
    illegal_chars = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]

    # Use a list comprehension to replace each illegal character with an underscore.
    sanitized = "".join([char if char not in illegal_chars else "_" for char in filename])

    return sanitized


def sleep_random(normal_seconds: int | None = None):
    """
    Sleep a random amount of time, based on the globally set normal duration
    """
    if normal_seconds is None:
        normal_seconds = G.SECONDS_TO_WAIT_BETWEEN_URL_READS

    if normal_seconds > 0:
        seconds_to_wait = random.triangular(normal_seconds * 0.5, normal_seconds * 1.5, normal_seconds)
        if seconds_to_wait > 0:
            print(f"Waiting {seconds_to_wait:1f} seconds before first try")
            sleep(seconds_to_wait)
            print("Resuming")


def parse_url_to_soup(url, image_downloader=None, wait_first_try=True):
    """Parse a URL and return the parsed DOM object"""

    # Must delay between reads for:
    # Carnegie Hall
    #

    # For sensitive websites, wait to avoid being blocked
    if wait_first_try:
        sleep_random()

    soup = None
    for i in range(G.NUM_URL_TRIES):
        try:
            selenium_loader = SeleniumLoader(False)
            soup = selenium_loader.soup_from_url(url)
            del selenium_loader
            selenium_loader = None
            if not soup:
                print("Selenium loader failed")
                continue

            if image_downloader:
                # This parser requires downloading the featured image, probably because the server does not allow
                # linking directly from our page.
                # We will upload these files to our server before whe importing the events CSV.
                folder, image_file_name, image_url = image_downloader(soup)
                image_file_name = sanitize_filename(image_file_name)
                if image_file_name:
                    full_image_path = get_full_image_path(folder, image_file_name)
                    if folder and image_file_name and image_url:
                        if not os.path.isfile(full_image_path):
                            # Read the image file from the server and store it as a file on the local drive
                            image_req = Request(image_url, headers=headers)
                            image = opener.open(image_req)
                            raw_image_data = image.read()
                            image.close()
                            with open(full_image_path, "wb") as saved_image_file:
                                print(f"Saving image {full_image_path}")
                                saved_image_file.write(raw_image_data)
                        else:
                            print(f"Image {full_image_path} already exists")
                else:
                    print("No image file name")
        except Exception as ex:
            raise
            print(f"Unable to open URL {url}: {ex}")
            if i <= (G.NUM_URL_TRIES - 2):
                print(f"Waiting before try {i + 2} of {G.NUM_URL_TRIES}")
                sleep_random()
                print(f"Retrying")
                continue
            print("URL read failed")
            return None
        else:
            if i > 0:
                print(f"Try {i + 1} succeeded.")
            break

    return soup


def parse_html_to_soup(html):
    """Parse a URL and return the parsed DOM object"""
    soup = BeautifulSoup(html, "html.parser")
    return soup


def data_path(file_name: str) -> str:
    """Return the full path to a file in the data directory"""
    return str(Path("../data", file_name))


def any_match(needles: typing.Iterable[str], haystacks: typing.Iterable[str]):
    """Find whether any match exists, given a list of texts and a list of matching words.
    Matches on whole words.
    """

    if isinstance(needles, str):
        needles = (needles,)
    if isinstance(haystacks, str):
        haystacks = (haystacks,)

    for needle in needles:
        for haystack in haystacks:
            if re.search(r"\b" + re.escape(needle.lower()) + r"\b", haystack.lower()):
                return True
    return False


def check_contents_file(file_name: str) -> int:
    """Check whether the event contents file exists"""
    if not os.path.exists(file_name):
        # File does not exist
        return 0

    # Since the file is a CSV file, open it as a CSV file and check how many lines it has
    with open(file_name, encoding="utf-8") as event_page_file:
        csv_reader = csv.reader(event_page_file)

        # Read the last row to get the URL
        event_page_file.seek(0)
        all_rows = list(csv_reader)
        all_non_empty_rows = [row for row in all_rows if row != []]
        last_row = all_non_empty_rows[-1]

    # The number of existing events is the number of non-empty rows minus one for the header row
    num_events = len(all_non_empty_rows) - 1

    # The URL is the first element in the row
    last_url = last_row[0]

    # Offer three options: 1) quit 2) append to the file, or 3) overwrite the file
    print(f"Contents file {file_name} already exists with {num_events} events.")
    print(f"Last URL in file: {last_url}")
    print("Options:")
    print("1) Quit")
    print("2) Append to the file")
    print("3) Overwrite the file")
    response = input("1/2/3: ")
    if response == "1":
        raise RuntimeError(f"File {file_name} already exists. Quitting.")
    elif response == "2":
        # Appending to file
        if len(all_non_empty_rows) > len(all_rows):
            # To remove any empty rows at the end of the file, write all non-empty rows back to the file
            with open(file_name, "w", encoding="utf-8", newline="\n") as event_page_file:
                writer = csv.writer(event_page_file)
                for row in all_non_empty_rows:
                    writer.writerow(row)
        return num_events
    elif response == "3":
        os.remove(file_name)
        print(f"File {file_name} deleted")
        return 0
    else:
        raise RuntimeError(f"Invalid response {response}")


def write_pages_to_soup_file(urls, page_file_path, parser):
    """Parse all the URLs to pages and save them"""

    # Loop over all of the URLs
    num_lines_written = 0
    num_rows_in_contents_file = 0
    first_row = True
    for i, (num_urls, url) in enumerate(urls):
        # Remove the page file if it already exists
        if i == 0:
            num_rows_in_contents_file = check_contents_file(page_file_path)

        if i < num_rows_in_contents_file:
            # Skip URLs already processed
            continue

        if not url.strip():
            continue

        if False:
            # Filter rows. Set lower limit to the number we were hung on previously.
            stuck_on_number = 60
            if not (stuck_on_number <= (i + 1) <= 1000):
                continue

        print(f"Processing URL {i + 1}/{num_urls}, {url}")
        if hasattr(parser, "parse_image_url"):
            image_parser = parser.parse_image_url
        else:
            image_parser = None
        soup = parse_url_to_soup(url, image_parser, not first_row)
        first_row = False
        if soup:
            # Allow parsers to filter out unwanted events
            if hasattr(parser, "content_filter"):
                soup = parser.content_filter(soup)
            if not soup:
                continue
            # Open and append to the page file for each loop, so
            # we don't lose data if a website call never returns
            with open(page_file_path, "a", encoding="utf-8") as event_page_file:
                writer = csv.writer(event_page_file)
                if i == 0:
                    writer.writerow(("url", "soup"))
                writer.writerow((url, soup_to_str(soup)))
                num_lines_written += 1

    return


def parse_pages_to_events(page_file_path, parser):
    """
    Parse a stored CSV file with urls and pages to a list of event rows
    :param page_file_path: file containing stored event listings
    :param parser: parser to use when decoding the pages
    :return: list of event rows (dictionaries)
    """

    event_rows = []

    with open(page_file_path, encoding="utf-8") as event_page_file:
        csv.field_size_limit(10000000)
        csv_reader = csv.reader(event_page_file)
        for loop, row in enumerate(csv_reader):
            if loop == 0:
                # Skip header row
                continue
            if not row:
                continue

            if False:  # Limit rows, for test imports
                if not 0 < loop <= 7:
                    continue

            url, html = row
            url = url.strip()  # Remove ending newline
            print(f"Parsing page from {url}")
            soup = BeautifulSoup(html, "html.parser")
            event_row = parser.parse_soup_to_event(url, soup)
            if not event_row:
                continue
            event_row = filter_event_row(event_row)
            if not event_row:
                continue

            if False:
                # Limit date not too far into the future
                if event_row["start_timestamp"] > dt.datetime(year=2022, month=12, day=31):
                    print(f'Skipping event too far in the future: {event_row["start_timestamp"]}')
                    continue

            event_rows.append(event_row)

    return event_rows


def serve_pages_from_url_list(urls):
    """Return html pages from reading each page in a list of URLs"""
    # Events
    nr_succeeded_urls = 0
    for url in urls:
        try:
            soup = parse_url_to_soup(url)
        except Exception as ex:
            print("ERROR: Unable to parse url {0}: {1}".format(url, ex))
            raise

        yield url, soup


def serve_pages_from_file(file_name):
    """Return html pages from canned file"""
    with codecs.open(file_name, encoding="utf-8") as input_file:
        while True:
            next_line = input_file.readline()
            if not next_line:
                break
            if not next_line.strip():
                continue
            soup = parse_html_to_soup(next_line)
            yield None, soup


def read_urls(file_name):
    """
    Read URLs from a file
    :param file_name: file name
    :return: Yields a URL for each line
    """
    num_urls = 0
    with codecs.open(file_name, encoding="utf-8") as input_file:
        while True:
            url = clean_up_url(input_file.readline())
            if not url:
                break
            num_urls += 1
            yield url


def filter_event_row(csv_row):
    if not "relevant" in csv_row:
        set_relevant_from_dict(csv_row)

    if not csv_row["relevant"]:
        print(f'Skipping irrelevant event "{csv_row["event_name"]}"')
        return None

    if "start_timestamp" in csv_row and csv_row["start_timestamp"].date() < EARLIEST_DATE:
        # Skip past events
        print(f"Skipping past event")
        return None

    if "event_name" in csv_row:
        if "<b>" in csv_row["event_name"]:
            print("Filtering bold in title")
            csv_row["event_name"] = csv_row["event_name"].replace("<b>", "").replace("</b>", "")

        if "&amp;" in csv_row["event_name"]:
            csv_row["event_name"] = csv_row["event_name"].replace("&amp;", "&")

        csv_row["event_name"] = f'IMPORT {csv_row["event_name"]}'

    csv_row["event_description"] = csv_row["event_description"].replace("Join us", "Join").replace("join us", "join")

    return csv_row


def initialize_csv_dict(url: str) -> dict:
    # all_day_event, categories, end_date, end_time, event_cost, event_description,
    # event_name, event_phone, event_website, organizer_name, show_map,
    # show_map_link, start_date, start_time, venue_name
    csv_dict = {
        "categories": "Live musical performance",
        "show_map": "TRUE",
        "show_map_link": "FALSE",
        "event_website": url,
        "all_day_event": "FALSE",
    }
    return csv_dict


def remove_all(string_to_alter, matches):
    for match in matches:
        string_to_alter = string_to_alter.replace(match, "")
    return string_to_alter


def soup_to_str(soup):
    string = str(soup.encode("utf-8"), encoding="utf-8")
    return string


def encode_html(text):
    encoded = html.escape(text).encode("ascii", "xmlcharrefreplace")
    encoded = str(encoded, encoding="utf-8")
    return encoded


def utc_to_local(utc_dt):
    """
    https://stackoverflow.com/questions/4563272/convert-a-python-utc-datetime-to-a-local-datetime-using-only-python-standard-lib?rq=1
    :param utc_dt: UTC datetime
    :return: Local datetime
    """
    local_dt = utc_dt.replace(tzinfo=dt.timezone.utc).astimezone(tz=None)
    return local_dt


def set_start_end_fields_from_start_dt(csv_dict, start_dt, end_dt=None, minutes=None):
    if not end_dt:
        end_dt = start_dt + dt.timedelta(minutes=minutes if minutes is not None else 90)
    #
    # Bug in Tribe importer subtracts one day from the end date
    csv_dict["start_timestamp"] = start_dt
    csv_dict["start_date"] = start_dt.strftime("%B %d, %Y")
    csv_dict["end_date"] = (end_dt + dt.timedelta(days=1)).strftime("%B %d, %Y")
    csv_dict["start_time"] = start_dt.strftime("%I:%M %p")
    csv_dict["end_time"] = end_dt.strftime("%I:%M %p")


def parse_event_tags(csv_dict: dict, event_tags: list, event_text: str) -> str:
    """Parse event text for event tags"""
    tags = set(event_tags)
    lower_text = event_text.lower().replace("\r", " ").replace("\n", " ")
    if any_match(("open rehearsal",), lower_text):
        tags.add("Rehearsal")
    if any_match(("masterclass", "master class"), lower_text):
        tags.add("Master Class")
    if any_match(
        (
            "tenor",
            "countertenor",
            "baritone",
            "soprano",
            "opera",
            "voice",
            "vocal",
            "singer",
        ),
        lower_text,
    ):
        tags.add("Vocal")
        tags.add("Ensemble")
    if any_match("opera", lower_text):
        tags.add("Opera")
    if any_match("premiere", lower_text):
        tags.add("Premiere")
    if any_match("debut", lower_text):
        tags.add("Debut")
    if any_match(["symphony", "orchestra"], lower_text):  # Avoid hits on 'Orchestrated', etc.
        tags.add("Orchestra")
        tags.add("Ensemble")
    elif is_relevant_to_site_as_accompanied(lower_text):
        tags.add("Chamber Music")
        tags.add("Collaborative")
        tags.add("Ensemble")
    if any_match("organ", lower_text):  # Avoid hits on 'organized' etc.
        tags.add("Organ")
    if any_match("fortepiano", lower_text):
        tags.add("Fortepiano")
    if any_match("harpsichord", lower_text):
        tags.add("Harpsichord")
    if any_match("competition", lower_text):
        tags.add("Competition")
    if any_match(
        ("for two pianos", "four hand", "four hands", "four-hand", "four-hands"),
        lower_text,
    ):
        tags.add("Four Hand")
        tags.add("Ensemble")
    if any_match("pre-college", lower_text):
        tags.add("Young Performer")
    if any_match(["jazz", "saxophone"], lower_text):
        tags.add("Jazz")
    if csv_dict.get("event_cost", None) in (0, "0"):
        tags.add("Free")
    if any_match(
        ["orchestra", "opera", "fortepiano", "harpsichord", "chamber music"],
        " ".join(tags),
    ):
        tags.add("Classical")
    if any_match(["recommended for kids", "curated for kids"], lower_text):
        tags.add("Young Audience")
    if "Ensemble" in tags and "Classical" in tags:
        tags.add("Collaborative")
    if "Collaborative" in tags and "Orchestra" in tags:
        # Keyboard concerto with an orchestra is not really collaborative
        tags.remove("Collaborative")

    # Resolve conflicting tags
    if "Ensemble" in tags and "Solo" in tags:
        tags.remove("Solo")
    if "Chamber Music" in tags and "Orchestra" in tags:
        tags.remove("Chamber Music")

    event_tags.clear()
    for tag in tags:
        event_tags.append(tag)

    tags_str = ",".join(sorted(event_tags, key=lambda x: x.lower()))
    return tags_str


def set_tags_from_dict(csv_dict: dict, tags: list[str] | None = None) -> None:
    """Parse tags from an otherwise complete event dictionary"""
    event_text = csv_dict.get("event_description", "") + " " + csv_dict.get("event_name", "")
    event_tags = csv_dict.get("event_tags", None) or []
    if tags:
        event_tags += tags
    parse_event_tags(csv_dict, event_tags, event_text)
    csv_dict["event_tags"] = ",".join(event_tags)


def set_relevant_from_dict(event_dict, include_accompanied=False):
    """Return whether an event is relevant to the website"""
    if "start_timestamp" in event_dict and event_dict["start_timestamp"].date() < dt.date.today():
        # Past event
        print(f'Skipping event from {event_dict["start_timestamp"].date()}: {event_dict["event_name"]}')
        event_dict["relevant"] = False
        return False

    event_text = event_dict.get("event_description", "") + " " + event_dict.get("event_name", "")
    relevant = is_relevant_to_site(event_text)
    if (not relevant) and include_accompanied:
        relevant = is_relevant_to_site_as_accompanied(event_text)
    event_dict["relevant"] = relevant
    return relevant


def parse_price_range(pricing_text):
    """Parse a text containing zero or more prices into a single price or price range"""
    price_matches = re.findall("\$(\d+\.?(\d{2})?)", pricing_text)
    float_prices = sorted([float(price[0]) for price in price_matches])
    prices: list[str] = [""] * len(float_prices)
    for i in range(len(float_prices)):
        if int(float_prices[i]) == float_prices[i]:
            # An even dollar amount
            prices[i] = "{0:d}".format(int(float_prices[i]))
        else:
            # Inlcude cents
            prices[i] = "{0:.2f}".format(float_prices[i])

    if len(prices) and (prices[0] == prices[-1]):
        price = "{0}".format(prices[0])
    elif len(prices) > 1:
        price = "{0}-{1}".format(prices[0], prices[-1])
    else:
        price = ""

    return price


def is_relevant_to_site(haystack):
    """Returns whether a string is relevant to the website"""
    if isinstance(haystack, str):
        # Convert string to list
        haystack = [
            haystack,
        ]
    else:
        haystack = list(haystack)

    # fmt:off
    is_relevant = any_match(['piano', 'pianos', 'pianist', 'pianists',
                             'organ', 'organs',
                             'harpsichord', 'harpsichords',
                             'fortepiano', 'fortepianos',
                             'clavichord', 'clavichords', 'celesta', 'celestas'],
                            haystack)
    # fmt:on

    return is_relevant


def is_relevant_to_site_as_accompanied(haystack: typing.Iterable[str]) -> bool:
    """
    Returns whether a string is relevant to the website as an instrument that is normally accompanied by piano
    :param haystack: Words to sample to check whether the event is relevant
    :return: Whether the event is relevant as accompanied
    """
    if isinstance(haystack, str):
        # Convert string to list
        haystack = [
            haystack,
        ]
    else:
        haystack = list(haystack)

    # fmt:off
    words_to_match = ['alto', 'baritone', 'bass', 'bass clarinet', 'bassoon', 'cello', 'clarinet', 'composer',
                      'composition', 'contrabassoon', 'contralto', 'countertenor', 'double bass', 'english horn',
                      'flute', 'french horn', 'horn', 'mezzo', 'oboe', 'piccolo', 'saxophone', 'soprano', 'tenor',
                      'timpani', 'trombone', 'trumpet', 'tuba', 'viola', 'violin', 'liederabend', 'sonatenabend',
                      'winter songbook', 'pre-college chamber music', 'voice']
    # fmt:on

    is_relevant = any_match(words_to_match, haystack)

    return is_relevant


def replace_pattern(original_string: str, p_original: str, p_replace: str) -> str:
    """Replace a pattern in a string with another pattern

    Args:
        original_string (str): original string
        p_original (str): original pattern
        p_replace (str): replacement pattern

    Returns:
        str: string with the original pattern replaced by the replacement pattern
    """
    while p_original in original_string:  # Repeat replacement as long as the original pattern exists
        original_string = original_string.replace(p_original, p_replace)
    return original_string


def clean_up_url(url: str) -> str:
    """Clean up a URL by removing whitespace and trailing slashes

    Args:
        url: A URL

    Returns:
        A cleaned up URL
    """
    return url.strip().removesuffix("/")


def clean_up_urls(urls: list[str]) -> list[str]:
    """Clean up URLs by removing whitespace and trailing slashes

    Args:
        urls (list[str]): A list of URLs

    Returns:
        list[str]: A list of cleaned up URLs
    """
    return [clean_up_url(url) for url in urls if url.strip()]


def retrieve_upcoming_urls() -> list[str]:
    """Retrieve the URLs of the upcoming events from a MySQL database view"""
    # Reading database credentials from environment variables
    host = os.getenv("WEBSITE_DB_HOST")
    user = os.getenv("WEBSITE_DB_USER")
    password = os.getenv("WEBSITE_DB_PASSWORD")
    database = os.getenv("WEBSITE_DB_NAME")
    view_name = "upcoming_events_view"

    # Print out all connection parameters for debugging
    print(f"host: {host}, user: {user}, password: {password}, database: {database}")
    print(f"Reading existing URLs from the database")
    try:
        # Connect to the database
        connection = mysql.connector.connect(host=host, user=user, password=password, database=database)
        cursor = connection.cursor()
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return list()

    try:
        # Query the database
        cursor.execute(f"SELECT event_url FROM {view_name}")
        rows = cursor.fetchall()
    except Exception as e:
        print(f"Error querying the database: {e}")
        return list()
    finally:
        # Close the connection
        cursor.close()
        connection.close()

    if not rows:
        return list()

    # Return the URLs
    return [clean_up_url(row[0]) for row in rows]
