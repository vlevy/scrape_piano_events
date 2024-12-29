import datetime as dt
import logging
import re
from pathlib import PurePath

import bs4
from bs4 import BeautifulSoup
from dateutil import parser as dtparser

from EventParser import EventParser
from parser_common_code import (
    get_full_image_path,
    initialize_csv_dict,
    set_start_end_fields_from_start_dt,
    set_tags_from_dict,
)

logger = logging.getLogger(__name__)

venue_translations = {
    "Alice Tully Hall": "Alice Tully Hall at Lincoln Center",
    "Alice Tully Hall, Hauser Patron Salon": "Alice Tully Hall at Lincoln Center",
    "The Cathedral Church of St. John the Divine": "Cathedral of St. John the Divine",
    "Claire Tow Theater": None,
    "Clark Studio Theater": None,
    "Daniel & Joanna S. Rose Studio": "Daniel and Joanna S. Rose Studio at Lincoln Center",
    "Daniel and Joanna S. Rose Studio": "Daniel and Joanna S. Rose Studio at Lincoln Center",
    "David Geffen Hall": "David Geffen Hall at Lincoln Center",
    "Kenneth C. Griffin Sidewalk Studio, David Geffen Hall": "David Geffen Hall at Lincoln Center",
    "David H. Koch Theater": None,
    "David Rubenstein Atrium": "David Rubenstein Atrium at Lincoln Center",
    "David Rubenstein Atrium at Lincoln Center": None,
    "Dizzy's Club Coca-Cola": None,
    "Dizzy's Club": "Dizzy's Club Coca-Cola",
    "Francesca Beale Theater": None,
    "Gerald W. Lynch Theater at John Jay College": None,
    "Merkin Hall": "Merkin Concert Hall at Kaufman Music Center",
    "Merkin Hall, Kaufman Music Center": "Merkin Concert Hall at Kaufman Music Center",
    "Metropolitan Opera House": None,
    "Mitzi E. Newhouse Theater": None,
    "Paul Recital Hall": "Juilliard School",
    "Peter Jay Sharp Theater": "Juilliard School",
    "Rosemary and Meredith Willson Theater": "Rosemary and Meredith Willson Theater",
    "Rose Theater": "Lincoln Center’s Rose Theater at Time Warner Center",
    "Rose Theater, Jazz at Lincoln Center’s Frederick P. Rose Hall": "Lincoln Center’s Rose Theater at Time Warner Center",
    "Samuel B. and David Rose Building": "Samuel B. & David Rose Building",
    "Samuel B. & David Rose Building": None,
    "Stanley H. Kaplan Penthouse": "Stanley H. Kaplan Penthouse at Lincoln Center",
    "Stephanie P. McClelland Drama Theater": None,
    "Stern Auditorium/Perelman Stage at Carnegie Hall": "Carnegie Hall",
    "The Appel Room": "The Appel Room at Lincoln Center",
    "The New York Public Library for the Performing Arts, Dorothy and Lewis B. Cullman Center, Donald and "
    "Mary Oenslager Gallery": "Donald and Mary Oenslager Gallery at Lincoln Center",
    "The New York Public Library for the Performing Arts, Dorothy and Lewis B. Cullman Center, Vincent Astor Gallery": "New York Public Library for the Performing Arts",
    "The New York Public Library for the Performing Arts, Dorothy and Lewis B. Cullman Center, Plaza Corridor Gallery": "New York Public Library for the Performing Arts",
    "The Peter Jay Sharp Theater": "Juilliard School",
    "Vivian Beaumont Theater": None,
    "Walter Reade Theater": "Walter Reade Theater at Lincoln Center",
    "Weill Recital Hall at Carnegie Hall": "Carnegie Hall",
    "Wu Tsai Theater, David Geffen Hall": "David Geffen Hall at Lincoln Center",
}


class LincolnCenterParser(EventParser):
    def parse_image_url(self, soup) -> tuple[str | None, str | None, str | None]:
        try:
            # https://res.cloudinary.com/nyphil/image/upload/c_fill%2Cg_auto%2Ch_1148
            # %2Cw_1640/f_auto/q_auto/v1705947816/images/concerts-tickets/calendar/2425
            # /EA1767_LisaMarieMazzucco?_a=BAAASyBs

            image_url = soup.find("img", attrs={"class": "event-header__image"})[
                "srcset"
            ]
            image_file_name = (
                re.search("/calendar/\d+/(.*)\?", image_url).groups()[0] + ".webp"
            )
            folder = "Lincoln_Center"
        except Exception as ex:
            image_url = "https://images.lincolncenter.org/image/upload/v1666888004/oning7nr84o4ud1zidzq.jpg"
            folder = None
            image_file_name = None
            # logger.info('No image URL found in {0}'.format(url))

        return folder, image_file_name, image_url

    def extract_performance_dates(self, soup_full: BeautifulSoup) -> list[dt.datetime]:
        soup: bs4.element.Tag | None = soup_full.find(
            "ul", attrs={"class": "event-info__performances"}
        )
        # Finding all <li> tags with class "performance"
        performance_items = soup.find_all("li", attrs={"class": "performance"})

        dates = []

        for performance in performance_items:
            # Extracting time
            time_tag = performance.find("span", class_="performance__time")
            time_text = time_tag.get_text(strip=True) if time_tag else ""

            # Extracting date, month, and year
            date_tag = performance.find("span", class_="performance__date")
            date_text = date_tag.get_text(strip=True) if date_tag else ""

            month_tag = performance.find("span", class_="performance__month")
            month_text = month_tag.get_text(strip=True) if month_tag else ""

            year_tag = performance.find("span", class_="performance__year")
            year_text = year_tag.get_text(strip=True) if year_tag else ""

            # Combine date and time into a single string
            full_date_str = f"{month_text} {date_text}, {year_text} {time_text}"

            # Convert string to datetime object (adjust format as needed)
            try:
                date_obj = dt.datetime.strptime(full_date_str, "%b %d, %Y %I:%M %p")
                dates.append(date_obj)
            except ValueError:
                # Handle invalid date formats if needed
                continue

        return dates

    def extract_programs(self, soup_full: BeautifulSoup) -> list[str]:
        # Find all program blocks
        program_blocks = soup_full.find_all("div", class_="program-panel__program")

        # Initialize a list to store program info
        programs = []

        # Loop through each program block and extract composer and work
        for program_div in program_blocks:
            composer_tag = program_div.find("h3", class_="program__title")
            work_tag = program_div.find("div", class_="program__details").find("p")

            # Extract and clean text
            composer = composer_tag.get_text(strip=True) if composer_tag else ""
            work = work_tag.get_text(strip=True) if work_tag else ""

            # Append work to the list
            programs.append(f"<strong>{composer}</strong> {work}")

        return programs

    def extract_performers(self, soup_full: BeautifulSoup) -> list[str]:
        # Find all performer blocks
        performer_blocks = soup_full.find_all(
            "div", class_="artist-accordion-block__item__header"
        )

        # Initialize a list to store performer info
        performers = []

        # Loop through each performer block and extract name and role
        for performer_div in performer_blocks:
            name_tag = performer_div.find("span", class_="artist-accordion-block__name")
            role_tag = performer_div.find("span", class_="artist-accordion-block__role")

            # Extract and clean text
            name = name_tag.get_text(strip=True) if name_tag else ""
            role = role_tag.get_text(strip=True) if role_tag else ""

            # Append performer to the list
            performers.append(f"<strong>{name}</strong> {role}")

        return performers

    def extract_festival_string(self, soup_full: BeautifulSoup) -> str:
        # Find the span with class "event-header__festival-tag"
        festival_span = soup_full.find("span", class_="event-header__festival-tag")

        # Extract the text and the anchor tag
        if festival_span:
            text_part = (
                festival_span.get_text(strip=True, separator=" ").split("Part of")[0]
                + "Part of "
            )
            anchor_tag = festival_span.find("a")
            if anchor_tag:
                anchor_href = anchor_tag["href"]
                anchor_text = anchor_tag.get_text(strip=True)
                anchor_string = f'<a href="{anchor_href}">{anchor_text}</a>'
            else:
                anchor_string = ""

            # Combine the text and the anchor string
            return text_part + anchor_string

        return ""

    def parse_soup_to_event(self, url, soup):
        # -----------------------------------
        # Easy fields
        # -----------------------------------
        event_tags = ["Classical"]

        csv_dict = initialize_csv_dict(url)

        # Event name
        event_name = soup.find("h1", class_="event-header__title").text.strip()
        if not event_name:
            raise RuntimeError("Unable to find event name")

        # ----------------------------------------------------------------
        # Date and time
        dates = self.extract_performance_dates(soup)
        start_dt = dates[0]
        set_start_end_fields_from_start_dt(csv_dict, start_dt)

        #
        # ----------------------------------------------------------------
        # Venue

        location_div = soup.find("div", class_="event-info__location")
        event_venue = location_div.find("p").get_text(strip=True)

        csv_dict["original_venue"] = event_venue
        csv_dict["venue_name"] = venue_translations[event_venue] or event_venue

        # If the venue is at Lincoln Center, just say "at Lincoln Center" in the title
        if "Lincoln Center" in csv_dict["venue_name"]:
            title_venue = "Lincoln Center"
        else:
            title_venue = csv_dict["venue_name"]
        csv_dict["event_name"] = f"{event_name}, at {title_venue}"

        # Event description other than performers and program
        description_lines = []
        try:
            description_lines.append(
                str(
                    soup.find(
                        "div", attrs={"class": "event-header__description"}
                    ).contents[0]
                )
            )
        except Exception as ex:
            logger.info(f"Unable to get the description, skipping")
            return None

        # Optional festival
        festival = self.extract_festival_string(soup)
        if festival:
            description_lines.append("")
            description_lines.append(festival)

        # Program
        program_lines = self.extract_programs(soup)
        if program_lines:
            description_lines.append("")
            description_lines.append("<strong>Program</strong>")
            for program in program_lines:
                description_lines.append(program)

        # Performers
        performers = self.extract_performers(soup)
        if performers:
            description_lines.append("")
            description_lines.append("<strong>Performers</strong>")
            for performer in performers:
                description_lines.append(performer)

        # Complete dates for a multi-date event
        if len(dates) > 1:
            description_lines.append("")
            description_lines.append("All performances:")
            for d in dates:
                description_lines.append(d.strftime("%b %d, %Y %I:%M %p"))

        # Complete description
        csv_dict["event_description"] = "\n".join(description_lines)

        # Image URL
        image_folder, image_file_name, image_url = self.parse_image_url(soup)
        full_image_path = get_full_image_path(image_folder, image_file_name)
        image_file_name = PurePath(full_image_path).name
        csv_dict["external_image_url"] = image_file_name

        # Tags
        set_tags_from_dict(csv_dict)

        return csv_dict
