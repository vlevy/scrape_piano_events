from pathlib import PurePath
import typing

from CarnegieHallParser import CarnegieHallParser
from JuilliardParser import JuilliardParser
from BargemusicParser_2 import BargemusicParser_2
from EventBriteParser_v2 import EventBriteParser_v2
from CmsParser import CmsParser
from SpectrumParser import SpectrumParser
from LincolnCenterParser import LincolnCenterParser
from NinetySecondsStreetYParser import NinetySecondsStreetYParser
from ScandinaviaHouseParser import ScandinaviaHouseParser
from MannesParser import MannesParser
from ZincParser import ZincParser
from KaufmanParser import KaufmanParser
from NjPacParser import NjPacParser
from NationalSawdustParser import NationalSawdustParser
from MsmParser import MsmParser
from NyplParser import NyplParser
from SymphonySpaceParser import SymphonySpaceParser
from BirdlandParser import BirdlandParser
from BlueNoteParser import BlueNoteParser

from parser_common_code import \
    serve_urls_from_file, \
    parse_pages_to_events, \
    write_event_rows_to_file, \
    write_pages_to_file

import importer_globals as G


def process_events(live_read_from_urls: bool, url_file_name: str, page_file_name: str, parser: typing.Callable):
    """Generic processor for different parsers
    """
    page_file_path = PurePath('Data', page_file_name)
    url_file_path = PurePath('Data', url_file_name)
    if live_read_from_urls:
        # Read all the individual page URLs
        urls = serve_urls_from_file(url_file_path)
        write_pages_to_file(urls, page_file_path, parser)
        return None
    else:
        # Read the HTML pages and parse them to events
        event_rows = parse_pages_to_events(page_file_path, parser)
        return event_rows


if __name__ == '__main__':
    '''Main program
    '''

    venue = 'BLUE_NOTE' # Last used June 13 2021
    venue = 'SYMPHONY_SPACE' # Last used Oct 9 2019
    venue = 'SPECTRUM' # Last used Oct 19 2019
    venue = 'MSM' # Last used Jan 1 2020
    venue = 'NYPL' # Last used Jan 25 2020. You have to extract the event URLs manually because the listing page
                   # makes it impossible to automate.
    venue = 'BIRDLAND' # Last used Feb 6 2020
    venue = 'MANNES' # Last used Oct 4 2021
    venue = 'NJPAC' # Last used Feb 12 2022
    venue = 'LINCOLN_CENTER'  # Last import 2022-03-21
    venue = 'BARGEMUSIC' # Last import valid through Aug 2022
    venue = 'ZINC-JAZZ' # Last used July 9 2022
    venue = '92Y' # Last used 2022-07-19
    venue = 'SCANDINAVIA_HOUSE' # Last used Jan 24 2020
    venue = 'CMS' # Last used Aug 3 2022
    venue = 'NATIONAL_SAWDUST' # Last used Aug 4 2022
    venue = 'BIRDLAND' # Last used Aug 5 2022
    venue = 'BARGEMUSIC' # Last used August 11 2022
    venue = 'EVENTBRITE' # Last used August 30 2022
    venue = 'KAUFMAN' # Last used August 31 2022
    venue = 'CARNEGIE' # Last used September 4 2022
    venue = 'JUILLIARD' # Last used September 7 2022

    LIVE_READ_FROM_URLS = False

    if venue == 'BARGEMUSIC':
        url_file_name = 'bargemusic_urls.txt'
        csv_page_contents_file_name = 'bargemusic_event_contents.csv'
        csv_rows = process_events(LIVE_READ_FROM_URLS, url_file_name, csv_page_contents_file_name, BargemusicParser_2())
    elif venue == 'CARNEGIE':
        G.NUM_URL_TRIES = 1
        url_file_name = 'carnegie-urls.txt'
        csv_page_contents_file_name = 'carnegie_event_contents.csv'
        csv_rows = process_events(LIVE_READ_FROM_URLS, url_file_name, csv_page_contents_file_name, CarnegieHallParser())
    elif venue == 'JUILLIARD':
        url_file_name = 'juilliard_urls.txt'
        csv_page_contents_file_name = 'juilliard_event_contents.csv'
        csv_rows = process_events(LIVE_READ_FROM_URLS, url_file_name, csv_page_contents_file_name, JuilliardParser())
    elif venue == 'EVENTBRITE':
        G.SECONDS_TO_WAIT_BETWEEN_URL_READS = 0
        url_file_name = 'eventbrite_event_urls.txt'
        parser = EventBriteParser_v2()
        if LIVE_READ_FROM_URLS:
            parser.read_urls(url_file_name)
        csv_page_contents_file_name = 'eventbrite_event_contents.csv'
        csv_rows = process_events(LIVE_READ_FROM_URLS, url_file_name, csv_page_contents_file_name, parser)
    elif venue == 'CMS':
        url_file_name = 'cms_event_urls.txt'
        csv_page_contents_file_name = 'cms_event_contents.csv'
        csv_rows = process_events(LIVE_READ_FROM_URLS, url_file_name, csv_page_contents_file_name, CmsParser())
    elif venue == 'LINCOLN_CENTER':
        G.SECONDS_TO_WAIT_BETWEEN_URL_READS = 20.0
        url_file_name = 'lincoln_center_event_urls.txt'
        csv_page_contents_file_name = 'lincoln_center_event_contents.csv'
        csv_rows = process_events(LIVE_READ_FROM_URLS, url_file_name, csv_page_contents_file_name, LincolnCenterParser())
    elif venue == '92Y':
        url_file_name = '92y_event_urls.txt'
        csv_page_contents_file_name = '92y_event_contents.csv'
        csv_rows = process_events(LIVE_READ_FROM_URLS, url_file_name, csv_page_contents_file_name,
                                  NinetySecondsStreetYParser())
    elif venue == 'SPECTRUM':
        url_file_name = 'spectrum_urls.txt'
        csv_page_contents_file_name = 'spectrum_event_contents.csv'
        csv_rows = process_events(LIVE_READ_FROM_URLS, url_file_name, csv_page_contents_file_name,
                                  SpectrumParser())
    elif venue == 'SCANDINAVIA_HOUSE':
        url_file_name = 'scandinavia-house_urls.txt'
        csv_page_contents_file_name = 'scandinavia-house_event_contents.csv'
        csv_rows = process_events(LIVE_READ_FROM_URLS, url_file_name, csv_page_contents_file_name,
                                  ScandinaviaHouseParser())
    elif venue == 'MANNES':
        G.SECONDS_TO_WAIT_BETWEEN_URL_READS = 120.0
        G.NUM_URL_TRIES = 2
        url_file_name = 'mannes_urls.txt'
        csv_page_contents_file_name = 'mannes_event_contents.csv'
        csv_rows = process_events(LIVE_READ_FROM_URLS, url_file_name, csv_page_contents_file_name,
                                  MannesParser())
    elif venue == 'ZINC-JAZZ':
        url_file_name = 'zinc-jazz-urls.txt'
        csv_page_contents_file_name = 'zinc_event_contents.csv'
        csv_rows = process_events(LIVE_READ_FROM_URLS, url_file_name, csv_page_contents_file_name,
                                  ZincParser())
    elif venue == 'KAUFMAN':
        url_file_name = 'kaufman-urls.txt'
        csv_page_contents_file_name = 'kaufman_event_contents.csv'
        parser = KaufmanParser()
        if False: # Kaufman website is unreliable for looking at future months
            if LIVE_READ_FROM_URLS:
                parser.read_urls(url_file_name)
        csv_rows = process_events(LIVE_READ_FROM_URLS, url_file_name, csv_page_contents_file_name, parser)
    elif venue == 'NJPAC':
        url_file_name = 'njpac_event_urls.txt'
        csv_page_contents_file_name = 'njpac_event_contents.csv'
        csv_rows = process_events(LIVE_READ_FROM_URLS, url_file_name, csv_page_contents_file_name, NjPacParser())
    elif venue == 'NATIONAL_SAWDUST':
        url_file_name = 'national_sawdust_urls.txt'
        csv_page_contents_file_name = 'national_sawdust_event_contents.csv'
        csv_rows = process_events(LIVE_READ_FROM_URLS, url_file_name, csv_page_contents_file_name, NationalSawdustParser())
    elif venue == 'MSM':
        url_file_name = 'msm_event_urls.txt'
        csv_page_contents_file_name = 'msm_event_contents.csv'
        csv_rows = process_events(LIVE_READ_FROM_URLS, url_file_name, csv_page_contents_file_name,
                                  MsmParser())
    elif venue == 'SYMPHONY_SPACE':
        url_file_name = 'symphony_space_event_urls.txt'
        csv_page_contents_file_name = 'symphony_space_event_contents.csv'
        csv_rows = process_events(LIVE_READ_FROM_URLS, url_file_name, csv_page_contents_file_name,
                                  SymphonySpaceParser())
    elif venue == 'NYPL':
        url_file_name = 'nypl_urls.txt'
        csv_page_contents_file_name = 'nypl_event_contents.csv'
        csv_rows = process_events(LIVE_READ_FROM_URLS, url_file_name, csv_page_contents_file_name,
                                  NyplParser())
    elif venue == 'BIRDLAND':
        url_file_name = 'birdland_urls.txt'
        csv_page_contents_file_name = 'birdland_event_contents.csv'
        csv_rows = process_events(LIVE_READ_FROM_URLS, url_file_name, csv_page_contents_file_name, BirdlandParser())
    elif venue == 'BLUE_NOTE':
        url_file_name = 'blue-note-urls.txt'
        csv_page_contents_file_name = 'blue-note_event_contents.csv'
        csv_rows = process_events(LIVE_READ_FROM_URLS, url_file_name, csv_page_contents_file_name, BlueNoteParser())
    else:
        raise ValueError(f'Invalid venue: "{venue}"')

    # Write rows to the Events Calendar CSV file
    if (not LIVE_READ_FROM_URLS) and csv_rows:
        file_name = 'import_events_{0}.csv'.format(venue)
        write_event_rows_to_file(file_name, csv_rows, max_num_rows=None)

    print(f"Done. {len(csv_rows or [])} events written total.")