import re
from datetime import date, datetime
from typing import List

from bs4 import BeautifulSoup

from EventParser import EventParser
from parser_common_code import (
    initialize_csv_dict,
    set_start_end_fields_from_start_dt,
    set_tags_from_dict,
)


def extract_dates_from_soup(soup: BeautifulSoup) -> List[datetime]:
    """
    Extracts dates in "Month day, year" format from a BeautifulSoup object
    within <time> tags located inside <div> elements with the class "group-listing".

    Args:
        soup (BeautifulSoup): A BeautifulSoup object containing parsed HTML content.

    Returns:
        List[datetime]: A list of datetime objects for each date found.
    """
    # Select the single <time> element within a <div> with the class "group-listing"
    time_tag = soup.select_one("div.group-listing time")

    # Extract date strings if time_tag is present
    date_strings = (
        re.findall(r"\b\w+ \d{1,2}, \d{4}\b", time_tag.get_text(strip=True))
        if time_tag
        else []
    )

    # Convert each date string to a datetime object using a list comprehension
    dates = [datetime.strptime(date_str, "%B %d, %Y") for date_str in date_strings]

    return dates


def parse_event_times(soup: BeautifulSoup):
    # Get current date and time
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    current_day = now.day

    # Find all event list items
    events = soup.find_all("li", class_="event")

    # Example event:
    #     <li class="event">
    #      <div class="ticket-wrap">
    #          <time><span class="day">Wed, Nov 27</span> <span class="time">8:00 PM</span>
    #          <span class="doors">(Doors 6:00 PM)</span></time>
    #          <a href="https://www.ticketweb.com/event/john-scofield-quartet-with-nicholas-blue-note-jazz-club-tickets/13466014?REFID=clientsitewp" class="buy-tickets">Buy Tickets</a>
    #      </div>
    #    </li>

    event_times = []
    for event in events:
        time_element = event.find("time")
        if time_element:
            day = time_element.find("span", class_="day").get_text(strip=True)
            time = time_element.find("span", class_="time").get_text(strip=True)

            # Combine day and time
            event_date_str = f"{day} {time}"
            # Parse the day string into a datetime object (year will be set to 1900)
            event_date = datetime.strptime(event_date_str, "%a, %b %d %I:%M %p")

            # Compare month and day, ignoring the year
            if (event_date.month < current_month) or (
                event_date.month == current_month and event_date.day < current_day
            ):
                event_date = event_date.replace(year=current_year + 1)  # Next year
            else:
                event_date = event_date.replace(year=current_year)  # Current year

            event_times.append(event_date)

    return event_times


class BlueNoteParser(EventParser):
    @staticmethod
    def parse_soup_to_event(url: str, soup: BeautifulSoup):
        """Parses a soup object into a dictionary whose keys are the CSV rows
        required by the imported CSV
        """

        # Easy fields
        csv_dict = initialize_csv_dict(url)
        venue = "Blue Note"
        csv_dict["venue_name"] = venue

        # Event name
        try:
            page_event_name = str(soup.find_all("h1")[0].contents[0])
        except Exception as e:
            logger.info(f"Error getting event name: {e}")
            return None

        page_event_name = " ".join(
            [word.capitalize() for word in page_event_name.lower().split()]
        )
        if not page_event_name:
            raise RuntimeError("Unable to get event name")
        if len(page_event_name) < 50:
            # No comma
            csv_dict["event_name"] = f"{page_event_name} at {venue}"
        else:
            # Comma
            csv_dict["event_name"] = f"{page_event_name}, at {venue}"

        # Description
        event_description = str(soup.find("div", attrs={"class": "event-description"}))
        if not event_description:
            raise RuntimeError("Unable to get event description")
        csv_dict["event_description"] = event_description

        # Tags
        csv_dict["event_tags"] = ["Jazz"]

        # Image
        # 'background:url(https://i.ticketweb.com/i/00/11/39/53/39_Edp.jpg?v=3) no-repeat;'
        # <img class="the-group-image" src="https://i.ticketweb.com/i/00/12/25/11/54_Edp.jpg?v=5" alt="John Scofield Quartet with Nicholas Payton featuring Vicente Archer &amp; Bill Stewart" width="640" height="427">
        #
        # Find the image in the div with class "the-group-image"
        img_tag = soup.find("img", attrs={"class": "the-group-image"})
        if img_tag:
            image_url = img_tag["src"]
            if "?" in image_url:
                # Split on a question mark and take the first part
                image_url = image_url.split("?")[0]
            csv_dict["external_image_url"] = image_url
        else:
            raise RuntimeError("Unable to find image")

        # -----------------------------
        # When
        #
        event_times = parse_event_times(soup)
        if not event_times:
            event_times = extract_dates_from_soup(soup)
            if not event_times:
                raise RuntimeError("Unable to get event date")
        set_start_end_fields_from_start_dt(csv_dict, event_times[0])
        recurring = len(event_times) > 1
        if recurring:
            csv_dict["event_tags"].append("Recurring")
            csv_dict["event_description"] += (
                "\n\nThis is a recurring event. All dates:\n"
            )
            additional_dates = "\n".join(
                [dt.strftime("%a, %b %d at %I:%M %p") for dt in event_times]
            )
            csv_dict["event_description"] += additional_dates

        # Price
        csv_dict["event_cost"] = "Check venue for pricing"

        # Special excemptions for relevancy
        artist_bios = str(soup.find_all("div", attrs={"class": "artist-bio"})).lower()

        if "pian" in artist_bios or "organ" in artist_bios or "keyboard" in artist_bios:
            csv_dict["relevant"] = True
        elif "glasper" in csv_dict["event_name"].lower():
            csv_dict["relevant"] = True

        set_tags_from_dict(csv_dict)

        return csv_dict
