import datetime as dt
import re

import bs4

from EventParser import EventParser
from parser_common_code import (
    initialize_csv_dict,
    set_start_end_fields_from_start_dt,
    set_tags_from_dict,
)


def extract_event_datetimes(soup: bs4.BeautifulSoup) -> list[dt.datetime]:
    """
    Extracts event date and time information from a BeautifulSoup object and returns a list of datetime objects.

    Parameters:
        soup (BeautifulSoup): Parsed BeautifulSoup object containing event information.

    Returns:
        list[datetime]: A list of datetime objects representing each event's date and time.

    Notes:
        If an event date is more than 6 months in the past relative to the current date, its year is incremented by one.
    """
    event_datetimes = []

    current_date = dt.datetime.now()

    for date_time_div in soup.select("div.tw-date-time"):
        date_str = date_time_div.select_one("span.tw-event-date").get_text(strip=True)
        time_str = (
            date_time_div.select_one("span.tw-event-time")
            .get_text(strip=True)
            .replace("Show: ", "")
        )

        # Combine and parse date and time
        combined_str = f"{date_str} {time_str}"
        event_datetime = dt.datetime.strptime(combined_str, "%a, %b %d %I:%M %p")

        # Initially parsed datetime has year 1900, replace with current year
        event_datetime = event_datetime.replace(year=current_date.year)

        # If the event date is more than 6 months in the past, roll forward by one year
        if (current_date - event_datetime) > dt.timedelta(days=182):
            event_datetime = event_datetime.replace(year=event_datetime.year + 1)

        event_datetimes.append(event_datetime)

    return event_datetimes


class BirdlandParser(EventParser):
    @staticmethod
    def parse_soup_to_event(url, soup):
        """Parses a soup object into a dictionary whose keys are the CSV rows
        required by the imported CSV
        """

        # Easy fields
        csv_dict = initialize_csv_dict(url)
        venue = "Birdland"
        csv_dict["venue_name"] = venue

        # Event name
        page_event_name = str(
            soup.find("div", attrs={"class": "tw-name"}).contents[0]
        ).strip()
        csv_dict["event_name"] = f"{page_event_name} at {venue}"

        # Image
        csv_dict["external_image_url"] = str(
            soup.find("img", attrs={"class": "event-img"})["src"]
        ).split("?")[0]

        # -----------------------------
        # When
        #
        event_datetimes = extract_event_datetimes(soup)
        start_dt = event_datetimes[0]
        set_start_end_fields_from_start_dt(csv_dict, start_dt)

        # Tags
        if len(event_datetimes) > 1:
            csv_dict["event_tags"] = "Jazz,Ensemble,Solo,Recurring"
        else:
            csv_dict["event_tags"] = "Jazz,Ensemble,Solo"

        # Description
        description_div = soup.select_one("div.tw-description")
        if description_div:
            description_text = "".join(
                str(child) for child in description_div.contents
            ).strip()
        else:
            description_text = ""

        if len(event_datetimes) > 1:
            description_text += "\n\nThis is a recurring event. All dates:\n"

            # Saturday, August 16 2025, 10:30 PM
            description_text += "\n".join(
                [d.strftime("%A, %B %d %Y, %I:%M %p") for d in event_datetimes]
            )

        csv_dict["event_description"] = description_text

        # -----------------------------
        # Price is not available

        return csv_dict
