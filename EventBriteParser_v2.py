import html
import json
import logging
from datetime import datetime
from pathlib import PurePath

from unidecode import unidecode

import importer_globals as G
from EventParser import EventParser
from parser_common_code import (
    encode_html,
    initialize_csv_dict,
    is_in_new_york,
    parse_price_range,
    parse_url_to_soup,
    retrieve_venues,
    set_relevant_from_dict,
    set_start_end_fields_from_start_dt,
    set_tags_from_dict,
    sleep_random,
)

logger = logging.getLogger(__name__)


class EventBriteParser_v2(EventParser):
    VENUES = {
        "468 W 143rd St": "Our Lady of Lourdes School",
        "790 11th Ave": "Klavierhaus",
        "790 11th Avenue": "Klavierhaus",
        "Alianza Dominicana Cultural Center": None,
        "ALPHAVILLE": None,
        "Artists Space": None,
        "Bar Freda": None,
        "Baruch Performing Arts Center": None,
        "Birdland Jazz Club": "Birdland",
        "Birdland Theater": "Birdland",
        "Bloomingdale School of Music": None,
        "Blue Gallery": None,
        "Bohemian National Hall": None,
        "Brooklyn Conservatory of Music": None,
        "Bruno Walter Auditorium": None,
        "Cafe Wha?": None,
        "Church in the Gardens": None,
        "Church of the Holy Apostles": None,
        "Church Of The Redeemer Astoria": "The Church of the Redeemer in Astoria",
        "CitySpire": None,
        "CRS (Center for Remembering & Sharing)": "CRS (Center for Remembering & Sharing)",
        "Cultural Center, Lycée Français de New York": "Lycée Français de New York",
        "DiMenna Center for Classical Music": None,
        "Dream House": None,
        "Fiction Bar/Cafe": None,
        "Fiorello H. LaGuardia High School of Music & Art and Performing Arts Concert Hall": "Fiorello H. LaGuardia High School of Music & Art and Performing Arts",
        "First Unitarian Church of Brooklyn": None,
        "First Unitarian Congregational Society in Brooklyn": None,
        "French Consulate in New York,": "Consulate General of France",
        "Good Judy": "skip",
        "Good Shepherd-Faith Presbyterian Church": None,
        "Groove": None,
        "Hoff-Barthelson Music School": "skip",
        "House of the Redeemer": None,
        "Hungarian House": None,
        "Hunter Hall": "skip",
        "Jamaica Center for Arts and Learning (JCAL)": "Jamaica Center for Arts and Learning",
        "Katra Lounge & Event Space": None,
        "Kaufman Music Center": "Merkin Concert Hall at Kaufman Music Center",
        "Klavierhaus NYC": "Klavierhaus",
        "Klavierhaus": None,
        "Kostabi World Chelsea": None,
        "Lamington Presbyterian Church": "skip",
        "Leonia United Methodist Church": None,
        "Louis Armstrong House Museum": None,
        "Mark Morris Dance Group": None,
        "Merkin Hall": "Merkin Concert Hall at Kaufman Music Center",
        "Michiko Rehearsal Studios": None,
        "Minton's Playhouse": None,
        "Morris Knolls High School": "skip",
        "Morristown": "skip",
        "Most Holy Redeemer Roman Catholic Church": None,
        "National Opera Center": "OPERA America's National Opera Center ",
        "New York Public Library for the Performing Arts -Bruno Walter Auditorium": "Bruno Walter Auditorium",
        "Old Stone House of Brooklyn": None,
        "ONX Studio": None,
        "OPERA America's National Opera Center Rehearsal Hall": "OPERA America's National Opera Center ",
        "OPERA America": "OPERA America's National Opera Center ",
        "Parkside Lounge": None,
        "Pequot Library": "skip",
        "Piano Works in Progress": None,
        "Pianos, Ludlow Street, New York, NY, USA": "skip",
        "Pianos": "skip",
        "Pino's Gift Basket Shoppe and Wine Cellar": "skip",
        "Pioneer Works": None,
        "PNC Bank Arts Center": "skip",
        "Quantum Brooklyn": None,
        "Rainbow Room": None,
        "Redeemer Episcopal Church": "The Church of the Redeemer in Astoria",
        "Roulette Intermedium": None,
        "Saint John's In the Village": "St. John's in the Village Episcopal Church",
        "Saint Peter's Church": "Saint Peter's Church",
        "Scholes Street Studio": None,
        "Soapbox Gallery": None,
        "South Presbyterian Church": None,
        "St John's in the village, St Benedict's Courtyard": "St. John's in the Village Episcopal Church",
        "St Paul's United Methodist Church": "St Paul's United Methodist Church",
        "St. John's in the Village Episcopal Church": "St. John's in the Village Episcopal Church",
        "St. John's in the Village": "St. John's in the Village Episcopal Church",
        "Tenri Cultural Institute of New York": "Tenri Cultural Institute",
        "Tenri Cultural Institute": None,
        "The Brick Presbyterian Church": None,
        "The Brooklyn Monarch": None,
        "The Church of the Transfiguration": None,
        "The College of New Jersey": "skip",
        "The Cutting Room": None,
        "The DiMenna Center for Classical Music": "DiMenna Center for Classical Music",
        "The Flamboyan Theater at The Clemente": "The Clemente Soto Vélez Cultural & Educational Center",
        "The Great Hall": "The Great Hall at Cooper Union",
        "The National Arts Club": None,
        "The National Jazz Museum in Harlem": "National Jazz Museum in Harlem",
        "The Presbyterian Church of Chatham Township": "skip",
        "The Stonewall Inn": None,
        "Theater at St. Jean": None,
        "Third Street Music School Settlement": None,
        "Threes Brewing": "Threes Brewing Greenpoint Bar & Beer Shop",
        "Topaz Arts Inc": None,
        "Ukrainian Institute of America": None,
        "Union Arts Center": "skip",
        "W83 Auditorium": "W83 Ministry Center",
        "West Side Presbyterian Church": "West Side Presbyterian Church in Ridgewood",
        "Willow Hall": "skip",
    }
    # Convert all keys to lowercase
    VENUES = {k.lower(): v for k, v in VENUES.items()}

    EXISTING_VENUES = retrieve_venues()

    @staticmethod
    def filter_event(soup):
        # If we got an expired event, don't use it
        ended = soup.find("class", attrs={"span", "expired-badge"})
        if ended:
            return None
        else:
            return soup

    @staticmethod
    def read_urls(url_file_name):
        """Read the event-page URLs for the first few pages of piano events in Manhattan"""
        urls = set()
        for page in range(5):
            sleep_random()
            url_this_page = f"https://www.eventbrite.com/d/ny--new-york/piano/?mode=search&page={page + 1}"
            logger.info("Reading URL {0}".format(url_this_page))

            soup = parse_url_to_soup(url_this_page)

            links = soup.find_all("a", attrs={"class": "event-card-link"})
            for link in links:
                url_this_event = link["href"].split("?")[0]
                urls.add(url_this_event)

        # Write the URLs out to a file for safekeeping
        url_file_path = PurePath("../Data", url_file_name)
        with open(url_file_path, "w", newline="\n") as url_file:
            for url_this_page in urls:
                url_file.write(url_this_page + "\n")

        return list(urls)

    @staticmethod
    def translate_venue(venue_from_page: str) -> str:
        # Replace any non-ASCII characters with their ASCII equivalents
        # For example, "&#39;" should be "'" and "&amp;" should be "&"
        venue1 = html.unescape(venue_from_page)
        if venue1 != venue_from_page:
            logger.info(f'1 Translated venue from "{venue_from_page}" to "{venue1}"')
        venue2 = unidecode(venue1)
        if venue2 != venue1:
            logger.info(f'2 Translated venue from "{venue1}" to "{venue2}"')
        venue3 = EventBriteParser_v2.VENUES.get(venue2.lower(), venue2) or venue2
        if venue3 != venue2:
            logger.info(f'3 Translated venue from "{venue2}" to "{venue3}"')

        return venue3

    @staticmethod
    def parse_soup_to_event(url, soup):
        """Parses a soup object into a dictionary whose keys are the CSV rows
        required by the imported CSV
        """

        csv_dict = initialize_csv_dict(url)

        # Details are stored in a JSON element
        try:
            event_json = soup.find_all("script", attrs={"type": "application/ld+json"})[
                1
            ].contents[0]
            # Some events have improperly encoded newlines
            event_json = event_json.replace("\t", " ")
            event_details = json.loads(event_json)
        except Exception as ex:
            logger.info(
                "Unable to parse event-details JSON in {0}: {1}".format(url, ex)
            )
            return None

        # Don't accept any events without a location
        try:
            latitude = float(
                soup.find("meta", attrs={"property": "event:location:latitude"})[
                    "content"
                ]
            )
            longitude = float(
                soup.find("meta", attrs={"property": "event:location:longitude"})[
                    "content"
                ]
            )
        except Exception as ex:
            logger.info("Listing location was not specified")
            return None

        tags_list = ["EB"]
        # "2018-03-25T17:00:00-04:00"
        try:
            date_string = event_details["startDate"][:19]
            start_dt = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S")
            if not start_dt:
                raise RuntimeError(f"Unable to find start date from {start_dt}")
            end_dt = datetime.strptime(
                event_details["endDate"][:19], "%Y-%m-%dT%H:%M:%S"
            )
            if not end_dt:
                raise RuntimeError(f"Unable to find end date from {start_dt}")
            set_start_end_fields_from_start_dt(csv_dict, start_dt, end_dt)
        except KeyError as ex:
            logger.info(f"Unable to parse start and/or end date: {ex}")
            return None

        try:
            csv_dict["event_name"] = "{0} at {1}".format(
                event_details["name"], event_details["location"]["name"]
            )
        except KeyError as ex:
            logger.info("Event name not found. Skipping.")
            return None

        venue_from_page = str(event_details["location"]["name"]).strip()
        venue = EventBriteParser_v2.translate_venue(venue_from_page)
        if venue == "skip":
            logger.info(f'Skipping event at unwanted venue "{venue_from_page}"')
            return None

        csv_dict["venue_name"] = venue
        csv_dict["organizer_name"] = event_details["organizer"]["name"]

        # Price
        free = False
        if "offers" in event_details:
            low = high = None
            if (
                "lowPrice" in event_details["offers"][0]
                and "highPrice" in event_details["offers"][0]
            ):
                low = event_details["offers"][0]["lowPrice"]
                high = event_details["offers"][0]["highPrice"]
            elif "price" in event_details["offers"][0]:
                low = high = event_details["offers"][0]["price"]

            if low is not None:
                if low == high:
                    csv_dict["event_cost"] = parse_price_range("${0}".format(low))
                else:
                    csv_dict["event_cost"] = parse_price_range(
                        "${0}-${1}".format(low, high)
                    )
                if low == 0:
                    free = True

        csv_dict["event_phone"] = None
        csv_dict["event_website"] = url
        csv_dict["show_map_link"] = False
        csv_dict["show_map"] = True

        # Event description
        try:
            description = "\n".join(
                str(c)
                for c in soup.find("div", attrs={"class": "eds-text--left"}).contents
            )
        except Exception as ex:
            try:
                summary = f"<strong>{event_details['description']}</strong>"
            except KeyError:
                logger.info("No description found")
                return None
            description_paragraphs = [summary, ""]
            description_paragraph_sections = soup.find_all(
                "div", attrs={"class": "structured-content-rich-text"}
            )
            if description_paragraph_sections:
                for section in description_paragraph_sections:
                    for i, p in enumerate(section.find_all("p")):
                        if p.contents:
                            description_paragraphs.append(
                                "".join([str(c) for c in p.contents])
                            )
                        else:
                            description_paragraphs += ""
            else:
                logger.info("Skipping event with only event summary available")
                return None
            description = f"<p>{'</p><p>'.join(description_paragraphs)}</p>"

        csv_dict["event_description"] = description

        if (
            "organizer" in event_details
            and "event_description" in event_details["organizer"]
        ):
            csv_dict["event_description"] += "\r\n" + encode_html(
                event_details["organizer"]["description"]
            )
        set_tags_from_dict(csv_dict, tags_list)
        if free:
            csv_dict["event_tags"] = ",".join((csv_dict["event_tags"], "Free"))

        if "image" in event_details:
            csv_dict["external_image_url"] = event_details["image"]
        else:
            logger.info("No image URL in {0}".format(url))

        # Filters
        if "at blue note" in csv_dict["event_name"].lower():
            return None
        if "at mezzrow" in csv_dict["event_name"].lower():
            return None
        if "at birdland jazz" in csv_dict["event_name"].lower():
            return None
        if "upstairs lounge" in csv_dict["event_name"].lower():
            return None
        if "dueling pianos" in csv_dict["event_name"].lower():
            return None
        if "pianos showroom" in csv_dict["event_name"].lower():
            return None
        if "ego free jam" in csv_dict["event_name"].lower():
            return None

        relevant = set_relevant_from_dict(csv_dict, include_accompanied=False)
        if not relevant:
            return None

        # Don't accept any events outside of New York
        if not is_in_new_york(latitude, longitude, venue):
            logger.info("Venue is outside of New York")
            return None

        # Hint to create venues
        if venue not in EventBriteParser_v2.EXISTING_VENUES:
            logger.info(f"Need to create venue {repr(venue)}")

        return csv_dict
