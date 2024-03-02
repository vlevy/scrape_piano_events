import re
from datetime import date, datetime

from EventParser import EventParser
from parser_common_code import (
    initialize_csv_dict,
    set_start_end_fields_from_start_dt,
    set_tags_from_dict,
)


class BlueNoteParser(EventParser):
    @staticmethod
    def parse_soup_to_event(url, soup):
        """Parses a soup object into a dictionary whose keys are the CSV rows
        required by the imported CSV
        """

        # Easy fields
        csv_dict = initialize_csv_dict(url)
        venue = "Blue Note"
        csv_dict["venue_name"] = venue

        # Event name
        page_event_name = str(soup.find_all("h1")[0].contents[0])
        page_event_name = " ".join([word.capitalize() for word in page_event_name.lower().split()])
        csv_dict["event_name"] = f"{page_event_name} at {venue}"

        # Description
        event_description = "\n".join([b.get_text().strip() for b in soup.find_all("td", attrs={"class": "text"})])
        csv_dict["event_description"] = event_description

        # Tags
        csv_dict["event_tags"] = ["Jazz"]
        set_tags_from_dict(csv_dict)

        # Image
        # 'background:url(https://i.ticketweb.com/i/00/11/39/53/39_Edp.jpg?v=3) no-repeat;'
        csv_dict["external_image_url"] = re.search(
            "background:url\((.+)[\?,\)]",
            soup.find("div", attrs={"class": "the-image"})["style"],
        ).groups()[0]

        # -----------------------------
        # When
        #
        try:
            # 'Sunday, March 15, 2020'
            date_str = str(soup.find("span", attrs={"class": "dates"}).contents[0])
            # 'Show: 7 PM'
            time_str = soup.find("span", attrs={"class": "start"}).contents[0].replace("Show: ", "")
            if ":" not in time_str:
                # Change 7 PM to 7:30 PM
                time_str = time_str[:-3] + ":00" + time_str[-3:]
            when_str = f"{date_str} {time_str}"
            start_dt = datetime.strptime(when_str, "%A, %B %d, %Y %I:%M %p")
            set_start_end_fields_from_start_dt(csv_dict, start_dt, minutes=90)
        except Exception as ex:
            print(f"Unable to get date/time")
        # -----------------------------

        # Price
        try:
            price_str = str(soup.find("span", attrs={"class": "price-range"}).contents[0])
            csv_dict["event_cost"] = price_str.replace("$", "").replace(" ", "").replace(".00", "")
        except Exception as ex:
            print(f"Unable to get price")

        return csv_dict
