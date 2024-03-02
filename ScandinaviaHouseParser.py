import datetime as dt
import re

from EventParser import EventParser
from parser_common_code import (
    initialize_csv_dict,
    set_start_end_fields_from_start_dt,
    set_tags_from_dict,
)


class ScandinaviaHouseParser(EventParser):

    def parse_soup_to_event(self, url, soup):
        # -----------------------------------
        # Easy fields
        # -----------------------------------
        event_tags = ["Classical"]
        csv_dict = initialize_csv_dict(url)
        csv_dict["venue_name"] = "Scandinavia House"

        # Event name
        event_name_parts = soup.find_all("h1", attrs={"class": "entry-title"})[0].contents

        event_name_part_1 = str(event_name_parts[0])
        if len(event_name_parts) > 1 and event_name_parts[1].contents:
            event_name_part_2 = str(event_name_parts[1].contents[0])
        else:
            event_name_part_2 = ""
        event_name = f'{event_name_part_1}{event_name_part_2}, at {csv_dict["venue_name"]}'
        # SH has the tendency to use all-caps
        event_name = " ".join([word.capitalize() for word in event_name.split()])
        csv_dict["event_name"] = event_name

        # Date: 'Thu—5-2-2019'
        date_str = str(soup.find_all("div", attrs={"class": "slide-event--large_date"})[0].contents[0])
        date_str = re.search("(?P<date>\d.+$)", date_str).group("date")
        start_str = f"{date_str} 20:00"
        try:
            start_dt = dt.datetime.strptime(start_str, "%m-%d-%Y %H:%M")
        except Exception as ex:
            print(f"Warning: Unable to determine starting time from  date: {repr(start_str)}")
            return None
        else:
            set_start_end_fields_from_start_dt(csv_dict, start_dt)

        # Event description
        paragraphs = [str(p) for p in soup.find("div", attrs={"class": ("event-content")}).contents[1].find_all("p")]
        description = "\n".join(paragraphs)
        csv_dict["event_description"] = description

        # Price
        print("WARNING: Check listing for correct price.")
        csv_dict["event_cost"] = "20-25"

        # Tags
        set_tags_from_dict(csv_dict, event_tags)

        # Image URL
        image_url = str(soup.find("meta", attrs={"property": "og:image"})["content"])
        csv_dict["external_image_url"] = image_url

        return csv_dict
