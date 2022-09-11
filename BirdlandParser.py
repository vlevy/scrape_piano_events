import re
import datetime as dt
from EventParser import EventParser
from parser_common_code import initialize_csv_dict, set_start_end_fields_from_start_dt, set_tags_from_dict
import bs4

class BirdlandParser(EventParser):

    @staticmethod
    def parse_soup_to_event(url, soup):
        """Parses a soup object into a dictionary whose keys are the CSV rows
        required by the imported CSV
        """

        # Easy fields
        csv_dict = initialize_csv_dict(url)
        venue = 'Birdland'
        csv_dict['venue_name'] = venue

        # Event name
        page_event_name = str(soup.find('h1', attrs={'class': 'tribe-events-single-event-title'}).contents[0])
        csv_dict['event_name'] = f'{page_event_name} at {venue}'

        # Description
        csv_dict['event_description'] = str(soup.find('div', attrs={'class': 'tribe-events-content'}).find_all('p')[0].contents[0])\

        # Tags
        csv_dict['event_tags'] = 'Jazz,Ensemble'

        # Image
        csv_dict['external_image_url'] = str(soup.find('img', attrs={'class': 'wp-post-image'})['src'])

        #-----------------------------
        # When
        #

        # 'startdt=2022-09-18T20:30:00&amp;enddt=2022-09-18T22:00:00'
        match = re.search(
            'startdt=(?P<start_year>20\d\d)-(?P<start_month>\d\d)-(?P<start_day>\d\d)T(?P<start_hour>\d\d):(?P<start_minute>\d\d):00&amp;'
            'enddt=(?P<end_year>20\d\d)-(?P<end_month>\d\d)-(?P<end_day>\d\d)T(?P<end_hour>\d\d):(?P<end_minute>\d\d):00',
            str(soup))
        start_dt = dt.datetime(int(match['start_year']),
                               int(match['start_month']),
                               int(match['start_day']),
                               int(match['start_hour']),
                               int(match['start_minute']))
        end_dt = dt.datetime(int(match['end_year']),
                               int(match['end_month']),
                               int(match['end_day']),
                               int(match['end_hour']),
                               int(match['end_minute']))

        set_start_end_fields_from_start_dt(csv_dict, start_dt, end_dt)
        #-----------------------------

        # Price is not available on the new site

        return csv_dict
