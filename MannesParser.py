import datetime as dt

from EventParser import EventParser
from parser_common_code import (
    initialize_csv_dict,
    is_relevant_to_site,
    is_relevant_to_site_as_accompanied,
    set_start_end_fields_from_start_dt,
    set_tags_from_dict,
    utc_to_local,
)

# Map venues in the listing to the exact venue name in the website
venue_map = {
    "": "Arnhold Hall at the New School",
    "1127 6th Ave, New York, NY 10036": "Steinway Hall",
    "Alice Tully Hall, Lincoln Center": "Alice Tully Hall at Lincoln Center",
    "Alice Tully Hall at Lincoln Center": "Alice Tully Hall at Lincoln Center",
    "Albert and Vera List Academic Center": "The New School, Albert and Vera List Academic Center",
    "Alvin Johnson/J.M. Kaplan Hall": "Alvin Johnson/J.M. Kaplan Hall",
    "Anna-Maria and Stephen Kellen Gallery, Sheila C. Johnson Design Center": "Anna-Maria and Stephen Kellen Gallery at Parsons School of Design",
    "Arnhold Hall": "Arnhold Hall at the New School",
    "Arnhold Hall, Glassbox Theater": "Arnhold Hall at the New School",
    "Baisley Powell Elebash Recital Hall, Arnold Hall": "Arnhold Hall at the New School",
    "Baisley Powell Elebash Recital Hall": "Arnhold Hall at the New School",
    "Baisley Powell Elebash Recital Hall (Room 750)": "Arnhold Hall at the New School",
    "Bohemian National Hall": "Bohemian National Hall",
    "Consulate General of Poland": "Consulate General of Poland",
    "Consulate of the Federal Republic of Germany": "Consulate General of Germany",
    "Ernst C. Stiefel Concert Hall": "Arnhold Hall at the New School",
    "Ernst C. Stiefel Hall at Arnhold Hall": "Arnhold Hall at the New School",
    "Eugene Lang College of Liberal Arts at The New School": "Eugene Lang College of Liberal Arts at The New School",
    "Gerald W. Lynch Theater at John Jay College": "Gerald W. Lynch Theater at John Jay College",
    "Gerald W. Lynch Theater": "Gerald W. Lynch Theater at John Jay College",
    "Gerald W Lynch Theater": "Gerald W. Lynch Theater at John Jay College",
    "German Consulate General, New York": "Consulate General of Germany",
    "Glassbox Theater": "Arnhold Hall at the New School",
    "House of the Redeemer": "House of the Redeemer",
    "Klein Conference Room, Room A510, Alvin Johnson/J.M. Kaplan Hall": "Alvin Johnson/J.M. Kaplan Hall",
    "Madison Avenue Presbyterian Church": "Madison Avenue Presbyterian Church",
    "Saint Jean Baptiste Church": "St. Jean Baptiste Church",
    "Sky Room, 12th floor": "Arnhold Hall at the New School",
    "Steinway": "Steinway Hall",
    "Steinway Hall": "Steinway Hall",
    "The Auditorium, Alvin Johnson/J.M. Kaplan Hall": "Alvin Johnson/J.M. Kaplan Hall",
    "The Auditorium, Room A106, Alvin Johnson/J.M. Kaplan Hall": "Alvin Johnson/J.M. Kaplan Hall",
    "The Grolier Club": "The Grolier Club",
    "The Union Club": "The Union Club",
    "Theresa Lang Community and Student Center, Arnhold Hall": "Arnhold Hall at the New School",
    "Union Square Park - North Plaza, NYC": "Union Square",
    "University Center": "The New School University Center",
    "Weill Recital Hall at Carnegie Hall": "Carnegie Hall",
    "Wollman Hall, Eugene Lang College": "Eugene Lang College of Liberal Arts at The New School",
}
# Map venues in the website to what to put in the post title, e.g., "Richard Goode Master Class, at Mannes"
venue_title_map = {
    "Alvin Johnson/J.M. Kaplan Hall": "The New School",
    "Parsons School of Design": "The New School",
    "Anna-Maria and Stephen Kellen Gallery at Parsons School of Design": "The New School",
    "Arnhold Hall at the New School": "The New School",
    "Bohemian National Hall": "the Bohemian National Hall",
    "Consulate General of Germany": "Consulate General of Germany",
    "Consulate General of Poland": "Consulate General of Poland",
    "Eugene Lang College of Liberal Arts at The New School": "The New School",
    "Glass Box Performance Space at the New School": "The New School",
    "House of the Redeemer": "House of the Redeemer",
    "John L. Tishman Auditorium, University Center": "The New School",
    "Alice Tully Hall at Lincoln Center": "Lincoln Center",
    "Madison Avenue Presbyterian Church": "Madison Avenue Presbyterian Church",
    "St. Jean Baptiste Church": "St. Jean Baptiste Church",
    "Carnegie Hall": "Carnegie Hall",
    "Steinway Hall": "Steinway Hall",
    "Union Square": "Union Square",
    "The Grolier Club": "The Grolier Club",
    "The New School": "The New School",
    "The Union Club": "The Union Club",
    "The New School University Center": "The New School",
    "The New School, Albert and Vera List Academic Center": "The New School",
    "Gerald W. Lynch Theater at John Jay College": "John Jay College",
}


class MannesParser(EventParser):

    def parse_soup_to_event(self, url, soup):
        csv_dict = initialize_csv_dict(url)
        csv_dict["organizer_name"] = "Mannes College of Music"
        event_tags = ["Classical", "Mannes"]

        # Venue
        try:
            venue_from_page = str(soup.find_all("div", attrs={"class": "venue-name"})[0].contents[0])
        except Exception as ex:
            print("Error: Venue not found")
            return dict()

        venue_name = venue_map[venue_from_page]
        csv_dict["venue_name"] = venue_name

        # Event name
        event_name = str(soup.find("title").contents[0])
        title_venue = venue_title_map[venue_name]

        event_name = f"Mannes Student Recital: {event_name}"
        if is_relevant_to_site_as_accompanied(event_name):
            event_name += " with Collaborative Piano"

        if title_venue != "The New School":
            event_name += f", at {title_venue}"
        csv_dict["event_name"] = event_name

        # Generic Mannes School image
        csv_dict["external_image_url"] = (
            "https://collegegazette.com/wp-content/uploads/2021/09/Mannes-School-of-Music-625x420.jpg"
        )

        # When
        month_str = soup.find("div", class_="date-month").text.strip()
        day_str = soup.find_all("div", class_="date-day")[-1].text.strip()
        year_str = soup.find("div", class_="date-year").text.strip()
        time_str = soup.find("div", class_="date-time").text.strip()
        date_str = f"{month_str} {day_str} {year_str} {time_str}"
        try:
            event_datetime = dt.datetime.strptime(date_str, "%B %d %Y %I:%M%p")
        except Exception as ex:
            print(f"Unable to parse event time from {date_str}")
            return dict()

        set_start_end_fields_from_start_dt(csv_dict, event_datetime)

        # Event description
        # Temporary
        description = soup.find("title").contents[0].text
        description = f'{description}\n\n\nTo attend this event, it\'s necessary to <a href="{url}">register here</a>.'
        csv_dict["event_description"] = description

        # Relevant
        relevant = is_relevant_to_site(str(description)) or is_relevant_to_site_as_accompanied(str(description))
        csv_dict["relevant"] = relevant

        # Price
        # TODO: Assume it's free
        price_string = "0"

        csv_dict["event_cost"] = price_string

        # Tags
        if "stone at the new school" in (event_name + description).lower():
            # These are not student performances
            event_tags.append("Avant-Garde")
            event_tags.append("Contemporary")
        else:
            event_tags += ["Student Recital"]

        set_tags_from_dict(csv_dict, event_tags)

        # Image URL

        return csv_dict
