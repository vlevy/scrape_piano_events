import json
import logging
from datetime import datetime

from EventParser import EventParser
from parser_common_code import (
    any_match,
    initialize_csv_dict,
    parse_url_to_soup,
    set_start_end_fields_from_start_dt,
    set_tags_from_dict,
)

logger = logging.getLogger(__name__)

VENUE_TRANSLATIONS = {
    "Merkin Concert Hall": "Merkin Concert Hall at Kaufman Music Center",
    "Merkin Hall": "Merkin Concert Hall at Kaufman Music Center",
}

COLLABORATIVE_HINTS = (
    "young-concert-artists-risa-hokamura-violin",
    "ukrainian-contemporary-music-festival-tribute-to-boris",
    "tuesday-matinees-kevin-zhu-violin",
    "new-york-philharmonic-ensembles",
    "asiya-korepanova-concert-pianist",
    "fast-forward-henry-schneider-concert",
    "fast-forward-chamberfest-2023",
    "contemporary-festival-2023",
    "kaufman-music-center-concerto-competition",
)


class KaufmanParser(EventParser):
    @staticmethod
    def parse_soup_to_event(url, soup):
        """Parses a soup object into a dictionary whose keys are the CSV rows
        required by the imported CSV
        """

        # Easy fields
        csv_dict = initialize_csv_dict(url)

        # Event JSON
        event_json_list = soup.find_all("script", attrs={"type": "application/ld+json"})
        if len(event_json_list) < 1:
            logger.info("Skipping because no JSON script was found")
            return None
        elif len(event_json_list) > 1:
            raise RuntimeError("Multiple JSON scripts found")

        event_json_str = str(event_json_list[0].contents)
        event_json_str = (
            event_json_str.replace("\\n", "\n")
            .replace("\\t", " ")
            .replace("\\r", "\n")
            .replace("'", "")
        )
        event_json_str = event_json_str.replace('"offers": \n  \n  "', '"\n  ')

        try:
            event_json = json.loads(
                event_json_str, strict=False
            )  # Allows newlines in quoted strings
            event_json = event_json[0]
        except Exception as ex:
            raise

        # Venue
        venue = event_json["location"]["name"]
        csv_dict["venue_name"] = VENUE_TRANSLATIONS[venue]

        # Event name
        event_name_from_page = event_json["name"]
        event_name = f"{event_name_from_page}, at {venue}"
        csv_dict["event_name"] = event_name

        # Special exemptions
        if any_match(COLLABORATIVE_HINTS, url):
            csv_dict["relevant"] = True

        # Date and time
        # Sunday | November 25 2018 | 6 pm
        start_dt = datetime.strptime(event_json["startDate"], "%Y-%m-%dT%H:%M")
        end_dt = datetime.strptime(
            event_json["endDate"], "%Y-%m-%dT%H:%M"
        )  # Unused because it's the same as start time
        set_start_end_fields_from_start_dt(csv_dict, start_dt)

        # Event description
        event_description = event_json["description"]
        csv_dict["event_description"] = event_description

        # Price
        if "offers" in event_json:
            try:
                price = event_json["offers"]["price"]
            except Exception as ex:
                price = event_json["offers"][-1]["price"]
            price = price.replace("$", "")
            csv_dict["event_cost"] = price

        # Image
        csv_dict["external_image_url"] = event_json["image"]

        # Tags
        set_tags_from_dict(csv_dict)

        return csv_dict
