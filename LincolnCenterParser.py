import datetime as dt
import json
import os
import re

from EventParser import EventParser
from parser_common_code import (
    initialize_csv_dict,
    set_start_end_fields_from_start_dt,
    set_tags_from_dict,
)

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

    def parse_soup_to_event(self, url, soup):
        # -----------------------------------
        # Easy fields
        # -----------------------------------
        event_tags = ["Classical"]

        csv_dict = initialize_csv_dict(url)

        # Event name
        event_name = soup.find("meta", attrs={"property": "og:title"})["content"]
        if not event_name:
            raise RuntimeError("Unable to find event name")

        # ----------------------------------------------------------------
        # Date and time

        # Check for a recurring event
        start_dt = None
        recurring = len(soup.find_all("p", attrs={"class": "eventDetailsReskin22__calendar-text--decorated"})) > 1
        try:
            day = int(soup.find("p", attrs={"class": "eventDetailsReskin22__calendar-text--decorated"}).contents[0])
            month = soup.find("p", attrs={"class": "eventDetailsReskin22__calendar-text--medium"}).contents[0]
            year = int(soup.find("p", attrs={"class": "eventDetailsReskin22__calendar-year"}).contents[0])
            time_text = soup.find_all("p", attrs={"class": "eventDetailsReskin22__calendar-text"})[1].contents[0]
            # '12-Oct-2022 7:30 PM'
            starttime_str = f"{day:02}-{month}-{year} {time_text}"
            start_dt = dt.datetime.strptime(starttime_str, "%d-%b-%Y %I:%M %p")
        except Exception as ex:
            pass

        if start_dt:
            set_start_end_fields_from_start_dt(csv_dict, start_dt)
        else:
            raise RuntimeError(f"Unable to get date/time from any section")

        #
        # ----------------------------------------------------------------
        # Venue
        event_venue = None
        try:
            event_venue = (
                soup.find("h2", attrs={"class": "eventDetailsReskin22__details-description"}).contents[0].strip()
            )
        except Exception as ex:
            pass
        if not event_venue:
            raise RuntimeError("Unable to match venue.")

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
                str(soup.find("p", attrs={"class": "event-detail-header-text-description"}).next.contents[0])
            )
        except Exception as ex:
            print(f"Unable to get the description, skipping")
            return None

        festival_link = soup.find("p", attrs={"class": "festival-link-text"})
        if festival_link:
            description_lines.append(str(festival_link.contents[0]))

        def listing_section(elem_left, class_left, elem_right, class_right):
            # Program or works or similar
            lines = list()
            left_html = soup.find_all(elem_left, attrs={"class": class_left})
            lefts = [f"<strong>{str(l.contents[0])}</strong>" if l.contents else None for l in left_html]
            lefts = list(filter(lambda x: x is not None, lefts))
            right_html = soup.find_all(elem_right, attrs={"class": class_right})
            rights = [str(r.contents[0]) if r.contents else None for r in right_html]
            if lefts and rights:
                lines = [f"{l} {r}" for l, r in zip(lefts, rights)]
            return lines

        # Program
        program_lines = listing_section(
            "h2",
            "eventDetailsReskin22__wrapper--programs-title",
            "p",
            "eventDetailsReskin22__wrapper--programs-details",
        )
        if program_lines:
            # Program heading
            program_lines = ["<strong>Program</strong>"] + program_lines

        # Performers
        performer_lines = listing_section("h3", "artist__title", "p", "artist__position")
        if performer_lines:
            # performer heading
            performer_lines = ["<strong>Artists</strong>\n"] + performer_lines

        section_end = "\n\n"
        full_event_text = ""
        if len(performer_lines) > 1:
            full_event_text += "\n".join(performer_lines) + section_end
        if len(program_lines) > 1:
            full_event_text += "\n".join(program_lines) + section_end
        if len(description_lines) > 0:
            full_event_text += "\n".join(description_lines) + section_end

        csv_dict["event_description"] = full_event_text

        # Price
        try:
            price = (
                soup.find_all("span", attrs={"class": "ticket-time-price"})[-1]
                .contents[0]
                .strip()
                .replace("$", "")
                .replace(" ", "")
                .replace("–", "-")
            )
        except Exception as ex:
            pass
        else:
            csv_dict["event_cost"] = price

        # Tags
        set_tags_from_dict(csv_dict)
        if recurring:
            csv_dict["event_tags"] += f",Recurring"

        # Image
        image_url = soup.find("meta", attrs={"property": "og:image"})["content"]
        if image_url:
            csv_dict["external_image_url"] = image_url

        return csv_dict
