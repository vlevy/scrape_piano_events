import datetime as dt
import json
import os
import re

from EventParser import EventParser
from parser_common_code import initialize_csv_dict, set_start_end_fields_from_start_dt


class NationalSawdustParser(EventParser):

    def parse_soup_to_event(self, url, soup):
        # -----------------------------------
        # Easy fields
        # -----------------------------------
        csv_dict = initialize_csv_dict(url)

        # Magic JSON with a lot of event info
        event_json = json.loads(soup.find(text=re.compile("startDate")))[0]

        # ----------------------------------------------------------------
        # Venue
        event_venue = "National Sawdust"
        csv_dict["venue_name"] = event_venue

        try:
            # Event name
            event_name_sections = soup.find("div", attrs={"class": "col-md-10"}).find_all(("h1", "h2", "h3"))
            event_name_sections = [str(s.contents[0]) for s in event_name_sections]
            event_name = " ".join(event_name_sections)
            csv_dict["event_name"] = f"{event_name}, at {event_venue}"
        except Exception as ex:
            raise
        # ----------------------------------------------------------------
        # Date and time
        # '2019-03-20T19:00:00-04:00'

        start_when_str = event_json["startDate"]
        end_when_str = event_json["endDate"]
        start_dt = dt.datetime.strptime(start_when_str[:19], "%Y-%m-%dT%H:%M:%S")
        end_dt = dt.datetime.strptime(end_when_str[:19], "%Y-%m-%dT%H:%M:%S")
        set_start_end_fields_from_start_dt(csv_dict, start_dt, end_dt)

        # ----------------------------------------------------------------
        # Description
        #
        full_event_text = "".join([str(s) for s in soup.find("div", attrs={"class": "event-about"}).contents])
        csv_dict["event_description"] = full_event_text

        # Price

        # Tags
        set_tags_from_dict(csv_dict)

        # Image URL
        csv_dict["external_image_url"] = event_json["image"]

        return csv_dict
