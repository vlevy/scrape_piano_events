import logging
import re
from datetime import date, datetime

from EventParser import EventParser
from parser_common_code import (
    initialize_csv_dict,
    set_start_end_fields_from_start_dt,
    set_tags_from_dict,
)

logger = logging.getLogger(__name__)


class BargemusicParser(EventParser):
    @staticmethod
    def parse_soup_to_event(url, soup):
        """Parses a soup object into a dictionary whose keys are the CSV rows
        required by the imported CSV
        """

        # -----------------------------------
        # Easy fields
        # -----------------------------------
        csv_dict = initialize_csv_dict(url)
        csv_dict["venue_name"] = "Bargemusic"
        page_event_name = str(
            soup.find(
                "h1", attrs={"class": "tribe-events-single-event-title"}
            ).contents[0]
        )
        page_event_name = re.sub("^.* Series: ", "", page_event_name)
        page_event_name = re.sub("^.* Festival: ", "", page_event_name)
        page_event_name = re.sub("^\d ?pm:?. *", "", page_event_name)

        # Convert the title to lowercase
        page_event_name = page_event_name.lower()

        # Capitalize the first letter of every word
        page_event_name = re.sub(r"\b\w", lambda x: x.group(0).upper(), page_event_name)

        # Lowercase prepositions shorter than 4 characters after capitalization
        page_event_name = re.sub(
            r"\b(?:And|At|By|For|In|Of|On|Up|Via|With)\b",
            lambda x: x.group(0).lower(),
            page_event_name,
        )

        page_event_name = f"{page_event_name}, at Bargemusic"
        csv_dict["event_name"] = page_event_name

        # -----------------------------------
        # Description (works on all pages)
        # -----------------------------------

        # Grab the description container that encloses the event text
        desc_container = soup.find(
            "div", class_="tribe-events-single-event-description"
        )

        # Remove the “Back to concerts calendar” navigation link, if present
        for anchor in desc_container.find_all(
            "a",
            string=lambda s: s and "back to concerts calendar" in s.lower(),
        ):
            parent_p = anchor.find_parent("p")
            (parent_p or anchor).decompose()  # remove only the navigation element

        # Extract builder text blocks and keep each unique block once
        description_parts: list[str] = []
        seen_html: set[str] = set()

        for block in desc_container.select(".et_pb_text_inner"):
            html_block = str(block).strip()
            if html_block and html_block not in seen_html:
                seen_html.add(html_block)
                description_parts.append(html_block)

        # Combine parts into the final description field
        csv_dict["event_description"] = "\n".join(description_parts)

        # -----------------------------------
        # Image
        # -----------------------------------
        csv_dict["external_image_url"] = (
            "https://www.bargemusic.org/wp-content/uploads/barge-logo.png"
        )

        # -----------------------------------
        # Start date
        # -----------------------------------
        start_text = str(
            soup.find("span", attrs={"class": "tribe-event-date-start"}).contents[0]
        )
        try:
            # 'December 16 at 4:00 pm'
            year = date.today().year
            start_dt = datetime.strptime(f"{start_text} {year}", "%B %d at %I:%M %p %Y")
        except Exception as ex:
            try:
                "December 16, 2020 at 4:00 pm"
                start_dt = datetime.strptime(start_text, "%B %d, %Y at %I:%M %p")
            except Exception as ex:
                raise
        if False:
            if start_dt > datetime(2019, 10, 15):
                return None

        set_start_end_fields_from_start_dt(csv_dict, start_dt)

        # -----------------------------------
        # Cost
        # -----------------------------------
        csv_dict["event_cost"] = 0

        # -----------------------------------
        # Tags
        # -----------------------------------
        set_tags_from_dict(csv_dict, ["Classical"])

        return csv_dict
