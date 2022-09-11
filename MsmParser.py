import json
import os
import re
import datetime as dt

from parser_common_code import set_start_end_fields_from_start_dt, initialize_csv_dict

from EventParser import EventParser

class MsmParser(EventParser):
    """
    Parser for Manhattan School of Music
    """
    def parse_soup_to_event(self, url, soup):
        # -----------------------------------
        # Easy fields
        # -----------------------------------
        csv_dict = initialize_csv_dict(url)

        # Event name
        event_name = str(soup.find('h2', attrs={'class': 'leadText'}).contents[0])

        #----------------------------------------------------------------
        # Date and time
        # Feb 14, 2019 3:00 pm

        recurring = False
        when_str = (soup.find('h1', attrs={'class': 'smallEyebrow'}).contents[0])

        try:
            parsed_dt = re.sub('-.*$', '', when_str).strip()
            start_dt = dt.datetime.strptime(parsed_dt, '%b %d, %Y %I:%M %p')
        except ValueError as ex:
            raise
        if len(when_str) > 21:
            recurring = True
        set_start_end_fields_from_start_dt(csv_dict, start_dt)

        #----------------------------------------------------------------
        # Venue
        event_venue = 'Manhattan School of Music'
        csv_dict['venue_name'] = event_venue
        csv_dict['organizer_name'] = event_venue
        title_venue = event_venue
        csv_dict['event_name'] = f'{event_name}, at {title_venue}'


        #----------------------------------------------------------------
        # Description
        #
        content_module = soup.find_all('div', {'class': ('contentModule', )})
        if len(content_module) >= 3:
            full_event_text = ''.join([str(s) for s in soup.find_all('div', {'class': ('contentModule', )})[2].contents])
            csv_dict['event_description'] = full_event_text
        else:
            print('Missing full description')

        # Price
        try:
            free = soup.find(text='This event is <strong>FREE and open to the public</strong>')
        except AttributeError as ex:
            pass
        else:
            price = 0
            csv_dict['event_cost'] = price

        # Tags
        csv_dict['event_tags'] = ['Classical', 'MSM']
        set_tags_from_dict(csv_dict)
        if recurring:
            csv_dict['event_tags'] += f',Recurring'

        # Image URL
        try:
            image_url = soup.find('div', attrs={'class': 'imageModule_container'}).contents[1]['src']
        except AttributeError as ex:
            print('No image URL found')
        else:
            csv_dict['external_image_url'] = image_url

        return csv_dict
