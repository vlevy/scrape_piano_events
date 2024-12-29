import datetime as dt
import json
import logging
import re

from EventParser import EventParser
from parser_common_code import (
    initialize_csv_dict,
    parse_event_tags,
    set_start_end_fields_from_start_dt,
)

logger = logging.getLogger(__name__)

# "None" venue translation means key is already correct
VENUE_TRANSLATIONS = {
    "96th Street Library": None,
    "Bruno Walter Auditorium": None,
    "Ottendorfer Library": None,
    "Stavros Niarchos Foundation Library": None,
}


class NyplParser(EventParser):
    """
    New York Public Library parser.
    """

    def parse_soup_to_event(self, url, soup):
        csv_dict = initialize_csv_dict(url)
        tags_list = ["nypl"]

        # All of the metadata is in a JSON block following the Twitter tag
        twitter_tag = soup.find("meta", attrs={"name": "twitter:site:id"})
        if not twitter_tag:
            logger.info("No Twitter tag")
            return None
        json_element = twitter_tag.find_next_sibling(
            "script", attrs={"type": "application/ld+json"}
        )
        json_parsed = json.loads(
            json_element.contents[0].replace("\t", ""), strict=False
        )

        # Check for repeating -- follow up manually
        try:
            date_times = [
                str(l.contents[0])
                for l in soup.find("ul", attrs={"class": "program-date"}).find_all("li")
            ]
        except Exception as ex:
            # Not repeating
            pass
        else:
            # Repeating
            if not date_times:
                raise RuntimeError("No event date found")
            if len(date_times) > 1:
                tags_list.append("Repeating")

        # Date and time, '2019-05-07T12:00:00-04:00'
        when_str = json_parsed["startDate"][:16]
        start_dt = dt.datetime.strptime(when_str, "%Y-%m-%dT%H:%M")
        set_start_end_fields_from_start_dt(csv_dict, start_dt)

        # Image
        csv_dict["external_image_url"] = json_parsed["image"]["url"]

        # Description - remove some formatting characters and extra spaces and newlines
        description = json_parsed["description"]
        description = description.replace("&acirc;", "")
        description = description.replace("&Acirc;", "")
        description = description.replace("&nbsp;", " ")
        description = re.sub("  +", " ", description)
        description = re.sub("\n\n\n+", "\n\n", description)
        csv_dict["event_description"] = description

        # Price
        csv_dict["event_cost"] = 0

        # Venue
        page_venue = json_parsed["location"]["name"]
        if (
            # Work-around for invalid location coding of Stavros Niarchos Foundation Library
            page_venue == "Event Center"
            and (
                (
                    "location" in json_parsed
                    and "streetAddress" in json_parsed["location"]
                    and json_parsed["location"]["streetAddress"] == "455 Fifth Avenue"
                )
                or (
                    "location" in json_parsed
                    and "address" in json_parsed["location"]
                    and "streetAddress" in json_parsed["location"]["address"]
                    and json_parsed["location"]["address"]["streetAddress"]
                    == "455 Fifth Avenue"
                )
                or (
                    "address" in json_parsed
                    and "streetAddress" in json_parsed["address"]
                    and json_parsed["address"]["streetAddress"] == "455 Fifth Avenue"
                )
            )
            or (1 == 1)
        ):
            page_venue = "Stavros Niarchos Foundation Library"
        venue = VENUE_TRANSLATIONS[page_venue] or page_venue
        csv_dict["venue_name"] = venue

        # Event name
        event_name = json_parsed["name"].strip()
        csv_dict["event_name"] = f"{event_name}, at {venue}"
        if "Silent Clown" in event_name:
            event_name = f"Film with Live Piano: {event_name}"
            tags_list.append("Film")

        if "New York Opera Forum" in event_name:
            csv_dict["organizer_name"] = "New York Opera Forum"

        # Tags
        csv_dict["event_tags"] = parse_event_tags(
            csv_dict, tags_list, " ".join([event_name, description])
        )

        return csv_dict
