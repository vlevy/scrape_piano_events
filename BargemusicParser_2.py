import re
from datetime import date, datetime
from EventParser import EventParser
from parser_common_code import initialize_csv_dict, set_tags_from_dict, \
    set_start_end_fields_from_start_dt

class BargemusicParser_2(EventParser):

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
        csv_dict['event_cost'] = '35'
        page_event_name = str(soup.find('h1', attrs={'class': 'tribe-events-single-event-title'}).contents[0])
        csv_dict['event_name'] = f'{page_event_name}, at Bargemusic'

        description_lines = ['<strong>Program</strong>']
        try:
            for line in soup.find('div', attrs={'class': 'et_pb_text_inner'}).find('ul').find_all('li'):
                description_lines.append(str(line))
        except Exception as ex:
            print(f'Could not find ul/li fields')

        description_lines.append('')
        performer_line = None
        for p in soup.find('div', attrs={'class': 'et_pb_text_inner'}).find_all('p'):
            for line_contents in p.contents:
                line = str(line_contents)
                if '<em>' in line:
                    # Performer line is the only line in italics
                    performer_line = line
                else:
                    description_lines.append(line)

        if performer_line:
            description_lines.append('')
            description_lines.append('<strong>Performers</strong>')
            description_lines.append(performer_line)

        csv_dict['event_description'] = '\n'.join(description_lines)

        set_tags_from_dict(csv_dict)
        csv_dict['event_tags'] += ',Classical'

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

        return csv_dict
