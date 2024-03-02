import datetime as dt
import re
from pathlib import PurePath

from EventParser import EventParser
from parser_common_code import (
    get_full_image_path,
    initialize_csv_dict,
    set_start_end_fields_from_start_dt,
    set_tags_from_dict,
)


def parse_date(str_date):
    try:
        the_dt = dt.datetime.strptime(str_date, "%a, %b %d • %I%p")
    except Exception as ex1:
        try:
            the_dt = dt.datetime.strptime(str_date, "%a, %b %d • %I:%M%p")
        except Exception as ex2:
            the_dt = None

    return the_dt


class JazzOrgParser(EventParser):

    def parse_image_url(self, soup) -> str:
        try:
            image_url = [i.get("data-image") for i in soup.find_all("img") if i.get("data-image")][0]
            image_file_name = re.search(".+/(.+\.jpg)$", image_url).groups()[0]
            folder = "JazzOrg"
        except Exception as ex:
            image_url = "jazzdotorg.jpg"
            folder = None
            image_file_name = None

        return folder, image_file_name, image_url

    def parse_soup_to_event(self, url, soup):
        """Parses a soup object into a dictionary whose keys are the CSV rows
        required by the imported CSV
        """

        # -----------------------------
        # When
        #
        def replace_date(d):
            year = dt.date.today().year
            if d.month < dt.date.today().month:
                year += 1
            d = d.replace(year=year)
            return d

        # Start out
        csv_dict = initialize_csv_dict(url)

        # Venue
        if len(soup.find_all("a", attrs={"class": "sqs-block-image-link", "href": "/dizzys-club"})):
            venue = "Dizzy's Club"
        else:
            try:
                venue = str(str(soup.find_all("h3")[0].contents).split(" • ")[1]).replace("'", "").replace("]", "")
            except Exception as ex:
                print("Unable to parse venue")
                return None
        csv_dict["venue_name"] = venue

        dates = [
            parse_date(e.contents[0].strip().lower())
            for e in soup.find_all("a", attrs={"class": "sqs-block-button-element"})
        ]
        dates = [replace_date(d) for d in dates if d is not None]

        try:
            set_start_end_fields_from_start_dt(csv_dict, dates[0])
        except Exception as ex:
            print("Unable to parse dates")
            the_date = dt.datetime(2025, 1, 1, 20, 0)
            set_start_end_fields_from_start_dt(csv_dict, the_date)

        # Event name
        try:
            page_event_name = soup.find("h2", attrs={"class": "edp-title"}).contents[0]
        except Exception as ex:
            page_event_name = str(soup.find("h2", attrs={"data-preserve-html-node": "true"}).contents[0].strip())

        event_name = f"{page_event_name} at {venue}".replace("at The", "at the")
        csv_dict["event_name"] = event_name

        # Description
        event_description = "\n".join(
            [str(p.contents[0]) for p in soup.find_all("p", attrs={"class": "sqsrte-large"})]
        )
        event_description = event_description.replace("<strong>", "").replace("</strong>", "")
        csv_dict["event_description"] = event_description

        # Tags
        csv_dict["event_tags"] = ["Jazz"]
        set_tags_from_dict(csv_dict)

        # Image
        image_folder, image_file_name, image_url = self.parse_image_url(soup)
        full_image_path = get_full_image_path(image_folder, image_file_name)
        image_file_name = PurePath(full_image_path).name
        csv_dict["external_image_url"] = image_file_name

        return csv_dict
