import csv
import datetime as dt
import html
import re
import random
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen, build_opener, HTTPCookieProcessor
import codecs
from datetime import date, datetime
from time import sleep
import os
from http.cookiejar import CookieJar
import typing
from pathlib import Path, PurePath
from SeleniumLoader import SeleniumLoader

import importer_globals as G

MAX_PARSE_TRIES = 3
EARLIEST_DATE = date(2018, 10, 25)
EARLIEST_DATE = date.today()

selenium_loader: SeleniumLoader = None

# Event columns in the correct order for importing.
# UNDERSTAND THIS BEFORE CHANGING THE ORDER.
CSV_COLUMNS_ORDERED = (
    'event_name',
    'venue_name',
    'organizer_name',
    'start_date',
    'start_time',
    'end_date',
    'end_time',
    'all_day_event',
    'categories',
    'event_cost',
    'event_phone',
    'event_website',
    'show_map_link',
    'show_map',
    'event_description',
    'external_image_url',
    'event_tags',
    'relevant',
    'start_timestamp',
)

CSV_COLUMNS = {
    'event_name': 'Event Name',
    'venue_name': 'Event Venue Name',
    'organizer_name': 'Organizer Name',
    'start_date': 'Event Start Date',
    'start_time': 'Event Start Time',
    'end_date': 'Event End Date',
    'end_time': 'Event End Time',
    'all_day_event': 'All Day Event',
    'categories': 'Event Category',
    'event_cost': 'Event Cost',
    'event_phone': 'Event Phone',
    'event_website': 'Event Website',
    'show_map_link': 'Event Show Map Link',
    'show_map': 'Event Show Map',
    'event_description': 'Event Description',
    'external_image_url': 'external_image_url',
    'event_tags': 'Event Tags',
    'relevant': 'Relevant',
    'start_timestamp': 'Start Timestamp',
}


def parse_file_to_soup(file_path):
    """Parse a URL and return the parsed DOM object
    """
    page = Request.urlopen('file:///{0}'.format(file_path))
    soup = BeautifulSoup(page, 'html.parser')
    return soup

def get_full_image_path(folder, image_file_name):
    """Return the full path to a downloaded image file given the folder and original file name
    :param folder: Destination folder
    :param image_file_name: File name from website
    :return: Full path to downloaded image file
    """
    full_image_path = PurePath(folder, f'{folder}_{image_file_name}')
    return full_image_path

def parse_url_to_soup(url, image_downloader=None, wait_first_try=True):
    """Parse a URL and return the parsed DOM object
    """

    # Must delay between reads for:
    # Carnegie Hall
    #
    global selenium_loader

    # For sensitive websites, wait to avoid being blocked
    if wait_first_try and G.SECONDS_TO_WAIT_BETWEEN_URL_READS > 0:
        seconds_to_wait = random.triangular(G.SECONDS_TO_WAIT_BETWEEN_URL_READS * 0.5,
                                            G.SECONDS_TO_WAIT_BETWEEN_URL_READS * 1.5,
                                            G.SECONDS_TO_WAIT_BETWEEN_URL_READS)
        if seconds_to_wait > 0:
            print(f'Waiting {seconds_to_wait} seconds before first try')
            sleep(seconds_to_wait)
            print('Resuming')

    soup = None
    for i in range(G.NUM_URL_TRIES):
        try:
            user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0'
            headers = {'User-Agent': f'{user_agent}'}
            cookie_jar = CookieJar()
            opener = build_opener(HTTPCookieProcessor(cookie_jar))
            if False:
                # Reading the cookie prevents 302/infinite redirect loop errors
                print('Opening page')

                req = Request(url, headers=headers)
                page = opener.open(req)
                print('Reading page')
                raw_page = page.read().decode('utf8', errors='ignore')
                print('Closing page')
                page.close()
                soup = BeautifulSoup(raw_page, 'html.parser')
            elif True:
                if not selenium_loader:
                    selenium_loader = SeleniumLoader()
                soup = selenium_loader.soup_from_url(url)

            if hasattr(image_downloader, 'parse_image_url'):
                # This parser requires downloading the featured image, probably because the server does not allow
                # linking directly from our page.
                # We will upload these files to our server before whe importing the events CSV.
                print('Parsing page')
                folder, image_file_name, image_url = image_downloader.parse_image_url(soup)
                full_image_path = get_full_image_path(folder, image_file_name)
                if folder and image_file_name and image_url:
                    if not os.path.isfile(full_image_path):
                        # Read the image file from the server and store it as a file on the local drive
                        if not os.path.isdir(folder):
                            os.mkdir(folder)
                        image_req = Request(image_url, headers=headers)
                        image = opener.open(image_req)
                        raw_image_data = image.read()
                        image.close()
                        with open(full_image_path, 'wb') as saved_image_file:
                            saved_image_file.write(raw_image_data)

        except Exception as ex:
            raise
            print(f'Unable to open URL {url}: {ex}')
            if i <= (G.NUM_URL_TRIES - 2):
                if G.SECONDS_TO_WAIT_BETWEEN_URL_READS > 0:
                    seconds_to_wait = random.triangular(G.SECONDS_TO_WAIT_BETWEEN_URL_READS * 0.5,
                                                        G.SECONDS_TO_WAIT_BETWEEN_URL_READS * 1.5,
                                                        G.SECONDS_TO_WAIT_BETWEEN_URL_READS)
                    print(f'Waiting {seconds_to_wait} seconds before try {i + 2} of {G.NUM_URL_TRIES}')
                    sleep(seconds_to_wait)
                print(f'Retrying')
                continue
            print('URL read failed')
            return None
        else:
            if i > 0:
                print(f'Try {i + 1} succeeded.')
            break;

    return soup


def parse_html_to_soup(html):
    """Parse a URL and return the parsed DOM object
    """
    soup = BeautifulSoup(html, 'html.parser')
    return soup


def any_match(needles: typing.List[str], haystacks: typing.Iterable[str]):
    """Find whether any match exists, given a list of texts and a list of matching words.
    Matches on whole words.
    """

    if isinstance(needles, str):
        needles = (needles,)
    if isinstance(haystacks, str):
        haystacks = (haystacks,)

    for needle in needles:
        for haystack in haystacks:
            if (re.search(r'\b' + re.escape(needle.lower()) + r'\b', haystack.lower())):
                return True
    return False


def write_pages_to_file(urls, page_file_path, image_parser=None):
    """Parse all the URLs to pages and save them
    """

    # Loop over all of the URLs
    num_lines_written = 0
    for i, (num_urls, url) in enumerate(urls):
        # Remove the page file if it already exists
        if i == 0 and os.path.exists(page_file_path):
            raise RuntimeError(f'File {repr(page_file_path)} already exists. Remove it manually to avoid accidental deletion.')
        if not url.strip():
            continue

        # Filter rows. Set lower limit to the number we were hung on previously.
        if False:
            stuck_on_number = 41
            if not (stuck_on_number <= (i + 1) <= 1000):
                continue

        print(f'Processing URL {i + 1}/{num_urls}, {url}')
        soup = parse_url_to_soup(url, image_parser, i > 0)
        if soup:
            # Open and append to the page file for each loop, so
            # we don't lose data if a website call never returns
            with open(page_file_path, 'a', encoding='utf-8') as event_page_file:
                writer = csv.writer(event_page_file)
                if i == 0:
                    writer.writerow(('url', 'soup'))
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

    with open(page_file_path, encoding='utf-8') as event_page_file:
        csv.field_size_limit(10000000)
        csv_reader = csv.reader(event_page_file)
        for loop, row in enumerate(csv_reader):
            if loop == 0:
                # Skip header row
                continue
            if not row:
                continue

            if False:
                # Limit rows, for test imports
#                if not 10 < loop <= 30:
#                    continue
                if loop > 2:
                    break

            url, html = row
            url = url.strip() # Remove ending newline
#            print(f'Parsing HTML from URL {url}', end=' ')
            print(f'Parsing HTML previously read from URL {url}')
            soup = BeautifulSoup(html, 'html.parser')
            event_row = parser.parse_soup_to_event(url, soup)
            if not event_row:
                continue
            event_row = filter_event_row(event_row)
            if not event_row:
                continue
            event_rows.append(event_row)

    return event_rows


def serve_pages_from_url_list(urls):
    """Return html pages from reading each page in a list of URLs
    """
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
    """Return html pages from canned file
    """
    with codecs.open(file_name, encoding='utf-8') as input_file:
        while True:
            next_line = input_file.readline()
            if not next_line:
                break
            if not next_line.strip():
                continue
            soup = parse_html_to_soup(next_line)
            yield None, soup


def serve_urls_from_file(file_name):
    """Return URLs from a file of URLs
    """
    # First loop only to get the number of URLs
    num_urls = 0
    with codecs.open(file_name, encoding='utf-8') as input_file:
        while True:
            next_line = input_file.readline()
            if not next_line:
                break
            num_urls += 1

    # Serve the URLs
    with codecs.open(file_name, encoding='utf-8') as input_file:
        while True:
            next_line = input_file.readline()
            if not next_line:
                break
            yield num_urls, next_line.strip()


def filter_event_row(csv_row):

    if not 'relevant' in csv_row:
        set_relevant_from_dict(csv_row)

    if not csv_row['relevant']:
        print(f'Skipping irrelevant event')
        return None

    if 'start_timestamp' in csv_row and \
            csv_row['start_timestamp'].date() < EARLIEST_DATE:
        # Skip past events
        print(f'Skipping past event')
        return None

    if 'event_name' in csv_row:
        if '<b>' in csv_row['event_name']:
            print('Filtering bold in title')
            csv_row['event_name'] = csv_row['event_name'].replace('<b>', '').replace('</b>', '')

        if '&amp;' in csv_row['event_name']:
            print('Filtering escaped ampersands in title')
            csv_row['event_name'] = csv_row['event_name'].replace('&amp;', '&')

        csv_row['event_name'] = f'IMPORT {csv_row["event_name"]}'

    csv_row['event_description'] = (
        csv_row['event_description']
            .replace('Join us', 'Join')
            .replace('join us', 'join')
    )

    return csv_row


def initialize_csv_dict(url: str) -> dict:
    # all_day_event, categories, end_date, end_time, event_cost, event_description,
    # event_name, event_phone, event_website, organizer_name, show_map,
    # show_map_link, start_date, start_time, venue_name
    csv_dict = { \
        'categories': 'Live musical performance',
        'show_map': 'TRUE',
        'show_map_link': 'FALSE',
        'event_website': url,
        'all_day_event': 'FALSE',
    }
    return csv_dict


def write_event_rows_to_file(file_name, csv_rows, max_num_rows=None):
    """Write a list of CSV rows to an importer file
    This is the last step of the whole process.
    """
    output_csv = None
    file_name_no_ext = os.path.splitext(file_name)[0]
    file_ext = os.path.splitext(file_name)[1]
    num_rows_left = len(csv_rows)
    file_num = 0
#    for i, csv_row in enumerate(sorted(csv_rows, key=lambda x: x.get('start_timestamp', datetime.now()))):
    for i, csv_row in enumerate(csv_rows):
        if (max_num_rows is None and i == 0) or ((max_num_rows is not None) and not (i % max_num_rows)):
            if output_csv:
                print(f'Wrote {num_rows_written_to_file} events to CSV file {file_name_to_open}')
                output_csv.close()

            # Open the output file
            file_num += 1
            if max_num_rows:
                file_name_to_open = f'{file_name_no_ext}_{file_num:03d}{file_ext}'
            else:
                file_name_to_open = file_name
            output_csv = open(file_name_to_open, 'w', encoding='utf-8', newline='\n')
            num_rows_written_to_file = 0

            # Write column header row
            writer = csv.writer(output_csv)
            writer.writerow([CSV_COLUMNS[key] for key in CSV_COLUMNS_ORDERED])

        # Write rows to the Events Calendar CSV file
        writer.writerow([csv_row.get(key, "") for key in CSV_COLUMNS_ORDERED])
        num_rows_written_to_file += 1

    if output_csv:
        print(f'Wrote {num_rows_written_to_file} events to CSV file {file_name_to_open}')
        output_csv.close()


def remove_all(string_to_alter, matches):
    for match in matches:
        string_to_alter = string_to_alter.replace(match, '')
    return string_to_alter


def soup_to_str(soup):
    string = str(soup.encode('utf-8'), encoding='utf-8')
    return string


def encode_html(text):
    encoded = html.escape(text).encode('ascii', 'xmlcharrefreplace')
    encoded = str(encoded, encoding='utf-8')
    return encoded


def utc_to_local(utc_dt):
    """
    https://stackoverflow.com/questions/4563272/convert-a-python-utc-datetime-to-a-local-datetime-using-only-python-standard-lib?rq=1
    :param utc_dt: UTC datetime
    :return: Local datetime
    """
    local_dt = utc_dt.replace(tzinfo=dt.timezone.utc).astimezone(tz=None)
    return local_dt

def set_start_end_fields_from_start_dt(csv_dict, start_dt, end_dt = None, minutes=None):
    if not end_dt:
        end_dt = start_dt + dt.timedelta(minutes=minutes if minutes is not None else 90)
    #
    # Bug in Tribe importer subtracts one day from the end date
    csv_dict['start_timestamp'] = start_dt
    csv_dict['start_date'] = start_dt.strftime('%B %d, %Y')
    csv_dict['end_date'] = (end_dt + dt.timedelta(days=1)).strftime('%B %d, %Y')
    csv_dict['start_time'] = start_dt.strftime('%I:%M %p')
    csv_dict['end_time'] = end_dt.strftime('%I:%M %p')


def parse_event_tags(csv_dict: dict, event_tags: list, event_text: str) -> str:
    """Parse event text for event tags
    """
    tags = set(event_tags)
    lower_text = event_text.lower().replace('\r', ' ').replace('\n', ' ')
    if any_match(('open rehearsal',), lower_text):
        tags.add('Rehearsal')
    if any_match(('masterclass', 'master class'), lower_text):
        tags.add('Master Class')
    if any_match(('tenor', 'countertenor', 'baritone', 'soprano', 'opera', 'voice', 'vocal', 'singer'), lower_text):
        tags.add('Vocal')
        tags.add('Ensemble')
    if any_match('opera', lower_text):
        tags.add('Opera')
    if any_match('premiere', lower_text):
        tags.add('Premiere')
    if any_match('debut', lower_text):
        tags.add('Debut')
    if any_match(['symphony', 'orchestra'], lower_text):  # Avoid hits on 'Orchestrated', etc.
        tags.add('Orchestra')
        tags.add('Ensemble')
    elif is_pianyc_related_as_accompanied(lower_text):
        tags.add('Chamber Music')
        tags.add('Collaborative')
        tags.add('Ensemble')
    if any_match('organ', lower_text):  # Avoid hits on 'organized' etc.
        tags.add('Organ')
    if any_match('fortepiano', lower_text):
        tags.add('Fortepiano')
    if any_match('harpsichord', lower_text):
        tags.add('Harpsichord')
    if any_match('competition', lower_text):
        tags.add('Competition')
    if any_match(('for two pianos', 'four hand', 'four hands', 'four-hand', 'four-hands'), lower_text):
        tags.add('Four Hand')
        tags.add('Ensemble')
    if any_match('pre-college', lower_text):
        tags.add('Young Performer')
    if any_match(['jazz', 'saxophone'], lower_text):
        tags.add('Jazz')
    if csv_dict.get('event_cost', None) in (0, '0'):
        tags.add('Free')
    if any_match(['orchestra', 'opera', 'fortepiano', 'harpsichord', 'chamber music'], ' '.join(tags)):
        tags.add('Classical')
    if any_match(['recommended for kids', 'curated for kids'], lower_text):
        tags.add('Young Audience')
    if 'Ensemble' in tags and 'Classical' in tags:
        tags.add('Collaborative')
    if 'Collaborative' in tags and 'Orchestra' in tags:
        # Keyboard concerto with an orchestra is not really collaborative
        tags.remove('Collaborative')

    # Resolve conflicting tags
    if 'Ensemble' in tags and 'Solo' in tags:
            tags.remove('Solo')
    if 'Chamber Music' in tags and 'Orchestra' in tags:
        tags.remove('Chamber Music')

    event_tags.clear()
    for tag in tags:
        event_tags.append(tag)

    tags_str = ','.join(sorted(event_tags, key=lambda x: x.lower()))
    return tags_str


def set_tags_from_dict(csv_dict: dict, tags: (list, None) = None) -> None:
    """Parse tags from and otherwise complete event dictionary
    """
    event_text = csv_dict.get('event_description', '') + ' ' + csv_dict.get('event_name', '')
    event_tags = csv_dict.get('event_tags', None) or []
    if tags:
        event_tags += tags
    parse_event_tags(csv_dict, event_tags, event_text)
    csv_dict['event_tags'] = ','.join(event_tags)


def set_relevant_from_dict(event_dict, include_accompanied=False):
    """Parse tags from and otherwise complete event dictionary
    """
    event_text = event_dict.get('event_description', '') + ' ' + event_dict.get('event_name', '')
    relevant = is_pianyc_related(event_text)
    if (not relevant) and include_accompanied:
        relevant = is_pianyc_related_as_accompanied(event_text)
    event_dict['relevant'] = relevant
    return relevant


def parse_price_range(pricing_text):
    """Parse a text containing zero or more prices into a single price or price range
    """
    price_matches = re.findall('\$(\d+\.?(\d{2})?)', pricing_text)
    prices = sorted([float(price[0]) for price in price_matches])
    for i in range(len(prices)):
        if int(prices[i]) == prices[i]:
            # An even dollar amount
            prices[i] = '{0:d}'.format(int(prices[i]))
        else:
            # Inlcude cents
            prices[i] = '{0:.2f}'.format(prices[i])

    if len(prices) and (prices[0] == prices[-1]):
        price = '{0}'.format(prices[0])
    elif len(prices) > 1:
        price = '{0}-{1}'.format(prices[0], prices[-1])
    else:
        price = ''

    return price


def is_pianyc_related(haystack):
    """Returns whether a string is relevant to pianyc
    """
    if isinstance(haystack, str):
        # Convert string to list
        haystack = [haystack, ]
    else:
        haystack = list(haystack)

    is_relevant = any_match(['piano', 'pianos', 'pianist', 'pianists',
                             'organ', 'organs',
                             'harpsichord', 'harpsichords',
                             'fortepiano', 'fortepianos',
                             'clavichord', 'clavichords', 'celesta', 'celestas'],
                            haystack)
    return is_relevant


def is_pianyc_related_as_accompanied(haystack: [typing.Iterable, str]) -> bool:
    """
    Returns whether a string is relevant to pianyc as an instrument that is normally accompanied by piano
    :param haystack: Words to sample to check whether the event is relevant
    :return: Whether the event is relevant as accompanied
    """
    if isinstance(haystack, str):
        # Convert string to list
        haystack = [haystack, ]
    else:
        haystack = list(haystack)

    words_to_match = ['alto', 'baritone', 'bass', 'bass clarinet', 'bassoon', 'cello', 'clarinet',
                      'contrabassoon', 'contralto', 'countertenor', 'double bass', 'english horn', 'flute',
                      'french horn', 'horn', 'mezzo', 'oboe', 'piccolo', 'saxophone',
                      'soprano', 'tenor', 'timpani', 'trombone', 'trumpet', 'tuba', 'viola', 'violin',
                      'liederabend', 'sonatenabend', 'students of',
                      ]

    is_relevant = any_match(haystack, words_to_match)

    return is_relevant
