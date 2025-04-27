# Set up basic logging
import logging
from dataclasses import dataclass
from typing import Any, Callable, Optional

import importer_globals as G
from BargemusicParser import BargemusicParser
from basic_utils import clean_up_urls
from BirdlandParser import BirdlandParser
from BlueNoteParser import BlueNoteParser
from CarnegieHallParser import CarnegieHallParser
from CmsParser import CmsParser
from EventBriteParser_v2 import EventBriteParser_v2
from EventParser import EventParser
from JazzOrgParser import JazzOrgParser
from JuilliardParser import JuilliardParser
from KaufmanParser import KaufmanParser
from LincolnCenterParser import LincolnCenterParser
from MannesParser import MannesParser
from MsmParser import MsmParser
from NationalSawdustParser import NationalSawdustParser
from NinetySecondsStreetYParser import NinetySecondStreetYParser
from NjPacParser import NjPacParser
from NyplParser import NyplParser
from parser_common_code import (
    check_contents_file,
    data_path,
    parse_pages_to_events,
    serve_urls_from_file,
    write_event_rows_to_import_file,
    write_pages_to_soup_file,
)
from prior_urls import append_to_prior_urls_file
from ScandinaviaHouseParser import ScandinaviaHouseParser
from SpectrumParser import SpectrumParser
from SymphonySpaceParser import SymphonySpaceParser
from ZincParser import ZincParser

# Set up logging with a custom formatter including the current time to the second, severity, filename, function, and line number
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s|%(levelname)s|%(filename)s|%(funcName)s|%(lineno)d|%(message)s",
)

logger = logging.getLogger(__name__)
logger.info("Starting event importer")


def process_events(
    live_read_from_urls: bool,
    parser: EventParser,
    url_getter: Callable | None = None,
    last_urls: list[str] | None = None,
):
    """Generic processor for different parsers
    Args:
        live_read_from_urls: Whether to read the URLs' contents from their website
        parser: The parser to use
        url_getter: A callable that returns a list of URLs
        last_urls: A list of URLs to skip
    """
    if live_read_from_urls:
        # Read all the individual page URLs
        logger.info(f"Processing URL file {url_file_path}")
        if url_getter:
            urls = url_getter()
            # TODO: Write URLs to file
        else:
            urls = serve_urls_from_file(url_file_path)
        if last_urls:
            new_urls = list(set(urls) - set(last_urls))
            urls = new_urls
            logger.info(
                f"Skipping {len(new_urls) - len(urls)} URLs that were found in the last contents file"
            )
        else:
            new_urls = urls
        write_pages_to_soup_file(new_urls, csv_page_contents_file_path, parser)

        return None
    else:
        # Read the HTML pages and parse them to events
        event_rows = parse_pages_to_events(csv_page_contents_file_path, parser)
        return event_rows


if __name__ == "__main__":
    """Main program"""

    venue = "SYMPHONY_SPACE"  # Last used Oct 9 2019
    venue = "ZINC-JAZZ"  # Website unavailable Dec 31 2024
    venue = "NATIONAL_SAWDUST"  # Last used Aug 4 2022
    venue = "BIRDLAND"  # Last used Aug 5 2022
    venue = "NYPL"  # Last used Sept 1 2024. You have to extract the event URLs manually because the listing page
    # makes it impossible to automate.
    venue = "LINCOLN_CENTER"  # Last import 2024-09-02
    venue = "BARGEMUSIC"  # Last used Sep 14 2024
    venue = "BLUE_NOTE"  # Last used October 2024-10-27
    venue = "NJPAC"  # Last used Nov 3 2024
    venue = "MSM"  # Last used Nov 3 2024
    venue = "92Y"  # Last used Nov 17 2024
    venue = "CMS"  # Last used Nov 22 2024 through spring season
    venue = "MANNES"  # Not used but entered manually in early Dec 2024
    venue = "KAUFMAN"  # Last used Dec 28 2024
    venue = "JAZZ_ORG"  # Checked manually Dec 30 2024
    venue = "SCANDINAVIA_HOUSE"  # Last used Jan 11 2025
    venue = "JUILLIARD"  # Last used February 8 2025
    venue = "CARNEGIE"  # Last used March 15 2025
    venue = "EVENTBRITE"  # Last used April 17 2025

    LIVE_READ_FROM_URLS = False

    @dataclass
    class VenueInfo:
        parser: Any  # Assuming the parser can be any type, adjust as needed
        num_url_tries: Optional[int] = None
        seconds_to_wait: Optional[float] = None

    # Dictionary for venue configurations
    venue_configurations = {
        "92Y": VenueInfo(NinetySecondStreetYParser()),
        "BARGEMUSIC": VenueInfo(BargemusicParser()),
        "BIRDLAND": VenueInfo(BirdlandParser()),
        "BLUE_NOTE": VenueInfo(BlueNoteParser()),
        "CARNEGIE": VenueInfo(CarnegieHallParser(), 1, 120.0),
        "CMS": VenueInfo(CmsParser()),
        "EVENTBRITE": VenueInfo(EventBriteParser_v2(), None, 1),
        "JAZZ_ORG": VenueInfo(JazzOrgParser()),
        "JUILLIARD": VenueInfo(JuilliardParser()),
        "KAUFMAN": VenueInfo(KaufmanParser()),
        "LINCOLN_CENTER": VenueInfo(LincolnCenterParser(), None, 20.0),
        "MANNES": VenueInfo(MannesParser(), 2, 10.0),
        "MSM": VenueInfo(MsmParser()),
        "NATIONAL_SAWDUST": VenueInfo(NationalSawdustParser()),
        "NJPAC": VenueInfo(NjPacParser()),
        "NYPL": VenueInfo(NyplParser()),
        "SCANDINAVIA_HOUSE": VenueInfo(ScandinaviaHouseParser()),
        "SPECTRUM": VenueInfo(SpectrumParser()),
        "SYMPHONY_SPACE": VenueInfo(SymphonySpaceParser()),
        "ZINC-JAZZ": VenueInfo(ZincParser()),
    }

    # Usage example with the dictionary
    if venue in venue_configurations:
        info = venue_configurations[venue]

        # Calculate file names based on venue
        url_file_path = data_path(f"{venue.lower()}_urls.txt")
        csv_page_contents_file_path = data_path(f"{venue.lower()}_event_contents.csv")
        importer_file_path = data_path(f"import_events_{venue.lower()}.csv")

        if LIVE_READ_FROM_URLS:
            # Check if the contents file exists
            last_urls = check_contents_file(csv_page_contents_file_path)
        else:
            last_urls = None

        # Set global variables if they exist
        if info.num_url_tries is not None:
            G.NUM_URL_TRIES = info.num_url_tries
        if info.seconds_to_wait is not None:
            G.SECONDS_TO_WAIT_BETWEEN_URL_READS = info.seconds_to_wait

        # For a parser that has a read_urls method, call it to create the URLs file
        # (URLs are returned for debugging)
        if hasattr(info.parser, "read_urls") and LIVE_READ_FROM_URLS:
            urls = clean_up_urls(info.parser.read_urls(url_file_path))

        # Now call process_events with the relevant info
        csv_rows = process_events(
            LIVE_READ_FROM_URLS,
            info.parser,
            last_urls,
        )

        if csv_rows:
            # Append the URLs to the file with previously scraped URLs
            urls = [r["event_website"] for r in csv_rows]
            append_to_prior_urls_file(urls, url_file_path)

    else:
        raise ValueError(f'Invalid venue: "{venue}"')

    # Write rows to the Events Calendar CSV file
    if (not LIVE_READ_FROM_URLS) and csv_rows:
        write_event_rows_to_import_file(importer_file_path, csv_rows, max_num_rows=0)

    logger.info(
        f"Done. {len(csv_rows or [])} events written total to {importer_file_path}."
    )
