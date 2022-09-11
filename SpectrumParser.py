import json
import os
import re
from datetime import datetime

from EventParser import EventParser

class SpectrumParser(EventParser):

    def parse_soup_to_event(self, url, soup):
        # -----------------------------------
        # Easy fields
        # -----------------------------------
        csv_dict = { \
            'categories': LIVE_PERFORMANCE,
            'show_map': 'TRUE',
            'show_map_link': 'FALSE',
            'event_website': url,
        }

        # Event name
        venue = 'Spectrum'
        title = soup.find_all('title')[0].contents[0]
        csv_dict['event_name'] = f"{title}, at {venue}"

        # Entire description starts with 'Sun 16 Sep, 3:00 PM - 4:30 PM: '
        entire_description = str(soup.find('meta', attrs={'name': 'description'})['content'])

        match = re.match('^(\(?(?P<year>20[12][0-9])(\) )?)?(?P<date>.+)\, '
                         '(?P<start_time>.+(AM|PM)) - (?P<end_time>.+(AM|PM)): (?P<description>.*$)',
                         entire_description)
        if not match:
            print(f'Unable to parse date and time from "{entire_description}"')
            return None

        # If year is not specified in the listing, it means this year
        year = match.groupdict().get('year') or datetime.now().date().year
        date_text = f"{match.group('date')} {year}"
        start_time = match.group('start_time')
        end_time = match.group('end_time')
        try:
            start_dt = datetime.strptime(f"{date_text} {start_time}", '%a %d %b %Y %I:%M %p')
            end_dt   = datetime.strptime(f"{date_text} {end_time}", '%a %d %b %Y %I:%M %p')
        except Exception as ex:
            raise
        set_start_end_fields_from_start_dt(csv_dict, start_dt, end_dt=end_dt)

        # Venue
        csv_dict['venue_name'] = venue

        # Event description
        csv_dict['event_description'] = f'{title}<br />{entire_description}'

        # Price
        csv_dict['event_cost'] = '10-15'

        # Tags
        tags = ['Solo', 'Pure Keyboard', 'Classical', 'Contemporary']
        set_tags_from_dict(csv_dict, tags)

        # Image URL
        try:
            image_url = soup.find_all('meta', attrs={'itemprop': 'image'})[0]['content']
        except Exception as ex:
            image_url = 'http://www.spectrumnyc.com/site/jpg/logo/spectrum-logo.jpg'
        csv_dict['external_image_url'] = image_url

        return csv_dict
