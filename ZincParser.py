import datetime as dt
import logging

from EventParser import EventParser
from parser_common_code import (
    initialize_csv_dict,
    set_start_end_fields_from_start_dt,
    set_tags_from_dict,
)

logger = logging.getLogger(__name__)

# Map venues in the listing to the exact venue name in the website


class ZincParser(EventParser):
    def parse_soup_to_event(self, url, soup):
        # -----------------------------------
        # Easy fields
        # -----------------------------------
        event_tags = ["Classical"]
        csv_dict = initialize_csv_dict(url)

        # Venue
        title_venue = "Zinc Bar"
        csv_dict["venue_name"] = title_venue

        # Event name
        event_name = str(soup.find("h4", attrs={"class": "entry-title"}).contents[0])
        csv_dict["event_name"] = f"{event_name}, at {title_venue}"

        # Date and time: 'November 16, 2018'
        date_str = str(
            soup.find("div", attrs={"class": "offbeat-event-date"})
            .contents[3]
            .contents[0]
        )
        start_dt = dt.datetime.strptime(date_str, "%B %d, %Y")
        start_dt = start_dt.replace(hour=20, minute=0)
        set_start_end_fields_from_start_dt(csv_dict, start_dt)

        # Event description
        paragraphs = soup.find(
            "div", attrs={"class": "offbeat-event-content"}
        ).find_all("p")
        for p in paragraphs:
            p.attrs = {}
        description = "".join([str(p) for p in paragraphs])
        csv_dict["event_description"] = description

        # Price
        logger.info("Fill in price from description")

        # Tags
        set_tags_from_dict(csv_dict)

        # Image URL
        image_url = (
            soup.find("div", attrs={"class": "offbeat-event-featured-image"})
            .contents[1]["src"]
            .split("?")[0]
        )
        csv_dict["external_image_url"] = image_url

        return csv_dict
