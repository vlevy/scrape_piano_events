import re
from datetime import date, datetime

from EventParser import EventParser
from parser_common_code import (
    initialize_csv_dict,
    set_start_end_fields_from_start_dt,
    set_tags_from_dict,
)


class BargemusicParser(EventParser):

    @staticmethod
    def parse_soup_to_event(url, soup):
        """Parses a soup object into a dictionary whose keys are the CSV rows
        required by the imported CSV
        """

        # -----------------------------------
        # Easy fields
        # -----------------------------------
        csv_dict = initialize_csv_dict(url)
        csv_dict['venue_name'] = 'Bargemusic'
        page_event_name = str(soup.find('h1', attrs={'class': 'tribe-events-single-event-title'}).contents[0])
        page_event_name = re.sub("^.* Series: ", "", page_event_name)
        page_event_name = re.sub("^.* Festival: ", "", page_event_name)
        csv_dict['event_name'] = f'{page_event_name}, at Bargemusic'

        # Loop through each div and concatenate them into an HTML string
        divs = soup.find_all('div', class_='et_pb_text_inner')
        description = ""
        prev_div = ""
        for div in divs:
            str_div = str(div)
            # Skip duplicate lines
            if str_div == prev_div:
                print(f"Skipping duplicated line {str_div}")
                continue
            prev_div = str_div

            # Remove the link back
            p_to_remove = div.find('p', string='Back to concerts calendar')
            if p_to_remove:
                continue
            description += str_div
        if True:
            description = re.sub("\<div\>(\\n)*\<\/div\>", '\n', description)
            description = re.sub("(\\n){3,}", '\\n', description)

        csv_dict['event_description'] = description

        csv_dict['external_image_url'] = 'https://www.bargemusic.org/wp-content/uploads/barge-logo.png'

        start_text = str(soup.find('span', attrs={'class': 'tribe-event-date-start'}).contents[0])
        try:
            # 'December 16 at 4:00 pm'
            year = date.today().year
            start_dt = datetime.strptime(f'{start_text} {year}', '%B %d at %I:%M %p %Y')
        except Exception as ex:
            try:
                'December 16, 2020 at 4:00 pm'
                start_dt = datetime.strptime(start_text, '%B %d, %Y at %I:%M %p')
            except Exception as ex:
                raise
        if False:
            if start_dt > datetime(2019, 10, 15):
                return None

        set_start_end_fields_from_start_dt(csv_dict, start_dt)

        # Cost
        try:
            cost = re.search("Tickets: \$(\d+)", description).groups()[0]
        except Exception as ex:
            print(f"Unable to locate price: {ex}")
            cost = 0
        csv_dict['event_cost'] = cost

        set_tags_from_dict(csv_dict)
        csv_dict['event_tags'] += ',Classical'

        return csv_dict
