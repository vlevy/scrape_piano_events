import datetime as dt
import logging
import re

from EventParser import EventParser
from parser_common_code import (
    initialize_csv_dict,
    set_start_end_fields_from_start_dt,
    set_tags_from_dict,
)

logger = logging.getLogger(__name__)


class ScandinaviaHouseParser(EventParser):
    def parse_soup_to_event(self, url, soup):
        # -----------------------------------
        # Easy fields
        # -----------------------------------
        event_tags = ["Classical"]
        csv_dict = initialize_csv_dict(url)
        csv_dict["venue_name"] = "Scandinavia House"

        # Event name
        event_name_parts = soup.find_all(
            "h1", attrs={"class": "tribe-events-single-event-title"}
        )[0].contents

        event_name_part_1 = str(event_name_parts[0])
        if len(event_name_parts) > 1 and event_name_parts[1].contents:
            event_name_part_2 = str(event_name_parts[1].contents[0])
        else:
            event_name_part_2 = ""
        event_name = (
            f'{event_name_part_1}{event_name_part_2}, at {csv_dict["venue_name"]}'
        )
        # SH has the tendency to use all-caps
        event_name = " ".join([word.capitalize() for word in event_name.split()])
        csv_dict["event_name"] = event_name

        # Date and start time March 25, 7:30 pm, 2024'
        date_time_start = (
            (
                str(
                    soup.find_all("span", attrs={"class": "tribe-event-date-start"})[
                        0
                    ].contents[0]
                )
                .replace("—", "-")
                .replace("-", ", ")
            )
            + ", "
            + dt.date.today().strftime("%Y")
        )
        # String to parse looks like this: March 25, 7:30 pm, 2024
        start_dt = dt.datetime.strptime(date_time_start, "%B %d, %I:%M %p, %Y")
        if start_dt < dt.datetime.now():
            start_dt = start_dt.replace(year=dt.datetime.now().year + 1)

        set_start_end_fields_from_start_dt(csv_dict, start_dt)

        # Event description
        paragraphs = [
            str(p)
            for p in soup.find(
                "div", attrs={"class": ("tribe-events-single-event-description")}
            ).find_all("p")
        ]
        description = "\n".join(paragraphs)
        csv_dict["event_description"] = description

        # Price
        logger.info("WARNING: Check listing for correct price.")
        csv_dict["event_cost"] = "30"

        # Tags
        set_tags_from_dict(csv_dict, event_tags)

        # Image URL
        # Example srcset:
        # 'https://www.scandinaviahouse.org/wp-content/uploads/2023/08/Photo-Jeffrey-Siegel-at-the-piano-1_NEW-WEB-scaled.jpg 2560w'
        # 'https://www.scandinaviahouse.org/wp-content/uploads/2023/08/Photo-Jeffrey-Siegel-at-the-piano-1_NEW-WEB-640x262.jpg 640w'
        # 'https://www.scandinaviahouse.org/wp-content/uploads/2023/08/Photo-Jeffrey-Siegel-at-the-piano-1_NEW-WEB-960x393.jpg 960w'
        # 'https://www.scandinaviahouse.org/wp-content/uploads/2023/08/Photo-Jeffrey-Siegel-at-the-piano-1_NEW-WEB-768x315.jpg 768w'
        # 'https://www.scandinaviahouse.org/wp-content/uploads/2023/08/Photo-Jeffrey-Siegel-at-the-piano-1_NEW-WEB-1536x629.jpg 1536w'
        # 'https://www.scandinaviahouse.org/wp-content/uploads/2023/08/Photo-Jeffrey-Siegel-at-the-piano-1_NEW-WEB-2048x839.jpg 2048w'
        # 'https://www.scandinaviahouse.org/wp-content/uploads/2023/08/Photo-Jeffrey-Siegel-at-the-piano-1_NEW-WEB-200x82.jpg 200w'

        # Split each image entryu into the URL and the width
        srcset = soup.find("img", attrs={"class": "wp-post-image"})["srcset"].split(
            ", "
        )
        srcset = [
            (url, int(width.removesuffix("w")))
            for url, width in [srcset_entry.split(" ") for srcset_entry in srcset]
        ]

        # Find the image with the largest width
        image_url = max(srcset, key=lambda x: x[1])[0]
        csv_dict["external_image_url"] = image_url

        return csv_dict
