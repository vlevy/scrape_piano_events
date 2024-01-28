from datetime import datetime
import json
from bs4 import BeautifulSoup
from EventParser import EventParser
from parser_common_code import (
    initialize_csv_dict,
    set_start_end_fields_from_start_dt,
    parse_event_tags,
)

VENUE_TRANSLATIONS_FOR_VENUE = {
    "": "Lincoln Center",
    "Alice Tully Hall": "Alice Tully Hall at Lincoln Center",
    "David Geffen Hall": "David Geffen Hall at Lincoln Center",
    "Daniel and Joanna S. Rose Studio at CMS": "Daniel and Joanna S. Rose Studio at Lincoln Center",
    "Kaplan Penthouse": "Stanley H. Kaplan Penthouse at Lincoln Center",
    "Rosemary and Meredith Willson Theater": "Rosemary and Meredith Willson Theater at Juilliard School",
    "Daniel and Joanna S. Rose Studio": "Daniel and Joanna S. Rose Studio at Lincoln Center",
    "Rose Studio at CMS": "Daniel and Joanna S. Rose Studio at Lincoln Center",
    "Rose Studio": "Daniel and Joanna S. Rose Studio at Lincoln Center",
}


class CmsParser(EventParser):
    """Parser for the Chamber Music Society of Lincoln Center"""

    @staticmethod
    def read_urls():
        """Read the event-page URLs for the first 10 pages of piano events in Manhattan"""
        with open(
            "chamber_music_society_urls_spring_2018.txt", encoding="utf-8"
        ) as url_file:
            urls = url_file.readlines()

        return urls

    @classmethod
    def parse_image_url_from_soup(cls, soup: BeautifulSoup):
        """
        Parse the image URL and file name from a CMS soup.
        :param soup: Soup to parse
        :return: image url, image file name
        """
        try:
            image_url = str(soup.find_all("source")[0]["srcset"].split(", ")[0])
        except Exception as ex:
            print("Unable to parse image URL")
            return None, None
        image_file_name = image_url.split("/")[-1]

        if image_file_name.endswith("png"):
            # WordPress imports .png files and saves them as .jpg files
            image_file_name = f'{image_file_name.removesuffix("png")}jpg'
        elif image_file_name.endswith("?_a=AAAMiAI"):
            # No extension on some files
            image_file_name = image_file_name.replace("?_a=AAAMiAI", "")
            image_file_name = f"{image_file_name}.jpg"

        return image_url, image_file_name

    def parse_image_url(self, soup) -> tuple[str | None, str | None, str | None]:
        try:
            # https://res.cloudinary.com/cmslc/image/upload/c_fill,f_auto,g_auto,h_320,q_auto,w_480/v1/Radio/19-20%20Programs/102818_Juho_Pohjonen.jpg
            image_url, image_file_name = self.parse_image_url_from_soup(soup)
            folder = "CMS"
        except Exception as ex:
            image_url = "CMS_default.jpg"
            folder = None
            image_file_name = None
            raise RuntimeError(f"No image URL found in {image_url}")

        return folder, image_file_name, image_url

    @staticmethod
    def parse_soup_to_event(url, soup):
        """Parses a soup object into a dictionary whose keys are the CSV rows
        required by the imported CSV
        """

        # -----------------------------------
        # Easy fields
        # -----------------------------------
        csv_dict = initialize_csv_dict(url)

        # Venue
        venue = None
        try:
            venue = str(
                soup.find("p", attrs={"class": "concert-header__venue"}).contents[0]
            )
        except Exception as ex:
            for i, c in enumerate(
                json.loads(
                    soup.find("script", attrs={"type": "application/ld+json"}).contents[
                        0
                    ]
                )
            ):
                if "url" in c and "location" in c and url in c["url"]:
                    # Found the venue in the alternate location
                    venue = c["location"]
                    break

        if not venue:
            venue = ""
        venue = venue.removesuffix(".")
        try:
            csv_dict["venue_name"] = VENUE_TRANSLATIONS_FOR_VENUE[venue]
        except Exception as ex:
            print(f"No translation for venue {venue}")
            venue = ""

        # Organizer
        csv_dict["organizer_name"] = "Chamber Music Society of Lincoln Center"

        # When
        event_when = str(
            soup.find("p", attrs={"class": "concert-header__date"}).contents[0]
        )
        parsers = (
            "%a, %b %d, %Y, %I:%M %p",  # Sun, Jan 28, 2024, 5:00 pm
            "%A, %B %d %Y, %I:%M %p",
            "%A, %B %d, %I:%M %p",
            "%A, %B %d, %Y %I:%M %p",
            "%A, %B %d, %Y, %I:%M %p",
            "%B, %d, %Y, %I:%M %p",
        )
        for parser in parsers:
            try:
                event_dt = datetime.strptime(event_when, parser)
                # Parsed successfully
                break
            except Exception:
                pass
        else:
            print("Unable to parse date: {0}".format(event_when))
            event_dt = None
        if event_dt:
            set_start_end_fields_from_start_dt(csv_dict, event_dt, minutes=90)
        else:
            # Placeholder start date, so importer will accept it
            set_start_end_fields_from_start_dt(
                csv_dict, datetime(2024, 1, 1, 8, 0, 0), minutes=90
            )

        # $<span class="u-large">40</span>.00–$<span class="u-large">80</span>.00
        try:
            event_costs = [
                eval(s.contents[0])
                for s in soup.find(
                    "div", attrs={"class": "production-header__price"}
                ).find_all("span", attrs={"class": "u-large"})
            ]
        except Exception as ex:
            event_costs = [0]
        try:
            csv_dict["event_cost"] = "-".join(["{0}".format(c) for c in event_costs])
        except Exception as ex:
            raise
        csv_dict["event_website"] = url

        _, image_file_name = CmsParser.parse_image_url_from_soup(soup)
        csv_dict["external_image_url"] = image_file_name

        # --------------------------------------
        # Body

        def add_section_to_description(content):
            if not content:
                return
            for outer_content in content:
                for inner_content in outer_content:
                    if (
                        "program-panel__composer__name" in str(inner_content)
                        and hasattr(inner_content, "find_all")
                        and inner_content.find_all()
                        and inner_content.find_all()[0].has_key("class")
                        and inner_content.find_all()[0]["class"][0]
                        == "program-panel__composer__name"
                    ):
                        if len(inner_content.contents) == 1:
                            composer = f"<p><h4>{inner_content.contents[0].contents[0]}</h4></p>"
                        elif len(inner_content.contents) == 3:
                            composer = f"<p><h4>{inner_content.contents[0].contents[0]} {inner_content.contents[2].contents[0]}</h4></p>"
                        else:
                            raise RuntimeError("Check content for composer")
                        description_list.append(composer)
                    elif "program-panel__items" in str(inner_content):
                        work = str(inner_content.contents[0])
                        # work = f"<p>{inner_content.contents[0].contents[0].contents[0].contents[0]} {inner_content.contents[0].contents[0].contents[2].contents[0]}</p>"
                        description_list.append(work)
                    else:
                        description_list.append(str(inner_content))

        # Description
        description_list = list()
        add_section_to_description(
            soup.find("div", attrs={"class": "content-panel__body"})
        )
        description_list.append("\n\n<h2>Program</h2>")
        add_section_to_description(
            soup.find("div", attrs={"class": "program-panel__list"})
        )
        description_list.append("\n\n<h2>Performers</h2>")
        add_section_to_description(
            soup.find("div", attrs={"class": "people-panel__list"})
        )

        description = "".join(description_list)
        csv_dict["event_description"] = description

        # # Program
        # program_lines = list()
        # for item in program_contents:
        #     composer = str(item.contents[3])
        #     work = ' '.join([str(c).strip() for c in item.contents if not any(('svg>' in str(c),'<span' in str(c), not len(str(c).strip()), composer in str(c).strip()))])
        #     this_line = '{0} {1}'.format(composer, work)
        #     program_lines.append(this_line)
        #
        # if program_lines:
        #     description.append('')
        #     description.append('<strong>Program</strong>')
        #     for p in program_lines:
        #         description.append(p)
        #
        # # Performers
        # pianists = []
        # performer_items = soup.find_all('div', attrs={'class': 'artist-item__body'})
        # if performer_items:
        #     description.append('')
        #     if len(performer_items) == 1:
        #         description.append('<strong>Performer</strong>')
        #     else:
        #         description.append('<strong>Performers</strong>')
        #
        #     for performer_item in performer_items:
        #         performer = performer_item.find('h3', attrs={'class': 'artist-item__title'}).contents[0]
        #         if performer_item.find('span', attrs={'class': 'artist-item__instrument'}).contents:
        #             instrument = performer_item.find('span', attrs={'class': 'artist-item__instrument'}).contents[0]
        #         elif ins := performer_item.find('span', attrs={'class': 'artist-item__role'}) and ins.contents:
        #             instrument = performer_item.find('span', attrs={'class': 'artist-item__role'}).contents[0]
        #         else:
        #             instrument =  None
        #
        #         if performer and instrument:
        #             performer_line = f'{performer}, {instrument}'
        #         elif performer:
        #             performer_line = f'{performer}'
        #         description.append(performer_line)
        #
        # csv_dict['event_description'] = '\n'.join(description)
        # #
        # #--------------------------------------

        # Name
        name_from_page = soup.find(
            "h1", attrs={"class": "concert-header__title"}
        ).contents[0]
        event_name = "Chamber Music Society of Lincoln Center, {0}".format(
            name_from_page
        )
        # if False and pianists:
        #     # Call out the pianists
        #     event_name = '{0}; {1}, Piano'.format(event_name, ' and '.join(pianists))
        csv_dict["event_name"] = event_name

        # Tags
        tags = ["Classical", "Ensemble", "Chamber Music", "Collaborative"]
        parse_event_tags(csv_dict, tags, csv_dict["event_description"])
        if not event_dt:
            tags.append("check-date")
        csv_dict["event_tags"] = ",".join(tags)

        return csv_dict
