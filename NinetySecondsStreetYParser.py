import json
from datetime import datetime

from EventParser import EventParser
from parser_common_code import (
    initialize_csv_dict,
    parse_event_tags,
    serve_urls_from_file,
    set_start_end_fields_from_start_dt,
)

VENUE_TRANSLATIONS = {
    'The 92nd Street Y, New York': '92nd Street Y',
}

class NinetySecondStreetYParser(EventParser):

    def parse_soup_to_event(self, url, soup):
        # -----------------------------------
        # Easy fields
        # -----------------------------------
        event_tags = ['Classical']
        csv_dict = initialize_csv_dict(url)

        # Pull in the JSON for this event
        event_json = json.loads(soup.find_all('script', attrs={'type': 'application/ld+json'})[0].contents[0])
        if isinstance(event_json, list):
            # Sometimes there is a list of events, so we take the last one
            event_json = event_json[-1]

        # Easy fields
        csv_dict['event_name'] = f"{event_json['name']}, at 92Y"
        csv_dict['external_image_url'] = event_json['image']
        csv_dict['event_website'] = event_json['url']
        venue_from_page = event_json['location']['name']
        csv_dict["venue_name"] = csv_dict["venue_name"] = VENUE_TRANSLATIONS[venue_from_page]
        csv_dict['event_cost'] = f"{event_json['offers']['lowPrice']}+"

        # When
        # '11/19/2018 7:30:00 PM'
        start_dt = datetime.strptime(event_json['startDate'], '%m/%d/%Y %I:%M:%S %p')
        end_dt   = datetime.strptime(event_json['endDate'], '%m/%d/%Y %I:%M:%S %p')
        set_start_end_fields_from_start_dt(csv_dict, start_dt, end_dt)

        # Pre-program description
        description_div = soup.find('div', attrs={'class': ['content-panel', 's-prose']}).contents
        description = ''.join(str(l) for l in description_div)

        # Program
        program_list = soup.find_all('li', attrs={'class': 'audio-playlist__item'})
        if program_list:
            description += '\n<strong>Program</strong>\n'
        for program_item in program_list:
            program_line = ''
            composer = program_item.find('span', attrs={'class': 'audio-playlist-item__artist'})
            if composer and composer.contents and composer.contents[0].strip():
                composer = composer.contents[0]
                if composer.endswith(','):
                    composer = composer[:-1]
                program_line += f'<strong>{composer}</strong> '
            work = program_item.find('span', attrs={'class': 'audio-playlist-item__title'})
            if work.contents:
                program_line += f'{work.contents[0]}\n'
            description += program_line

        # Complete description is a combination of the pre-program and program
        csv_dict['event_description'] = description

        # Event tags
        event_tags = ["Classical"]
        event_text = '\n'.join((csv_dict['event_name'], csv_dict['event_description']))
        parse_event_tags(csv_dict, event_tags, event_text)
        csv_dict["event_tags"] = ",".join(event_tags)

        return csv_dict
