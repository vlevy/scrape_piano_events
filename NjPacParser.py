import re
import datetime as dt

from parser_common_code import initialize_csv_dict, set_start_end_fields_from_start_dt, set_tags_from_dict

from EventParser import EventParser

class NjPacParser(EventParser):

    def parse_soup_to_event(self, url, soup):
        # -----------------------------------
        # Easy fields
        # -----------------------------------
        csv_dict = initialize_csv_dict(url)
        event_tags = ['Classical']

        # Event name
        try:
            event_name = str(soup.find('title').contents[0]).replace(' - NJPAC', '')
        except AttributeError as ex:
            print(f'Unable to find event name. Skipping.')
            return None

        #----------------------------------------------------------------
        # Date and time

        recurring = False
        start_dt = None
        try:
            # 'Saturday, March 23, 2019'
            # '8:00 PM'
            if (len(soup.find_all('span', attrs={'class': 'date'}))) > 1:
                print("RECURRING EVENT -- MANUALLY ENTER RECURRING AND CHECK PRICE")
                recurring = True

            date_str = (soup.find('span', attrs={'class': 'date'}).contents[0])
            time_str = (soup.find('span', attrs={'class': 'time'}).contents[0])
            start_dt = dt.datetime.strptime(f'{date_str} {time_str}', '%A, %B %d, %Y %I:%M %p')
        except Exception as ex:
            pass

        if start_dt is None:
            # 'Fri, 02/21/20 @ 8:00pm
            dl = soup.find('dl', attrs={'class': 'event-details-list__performances'})
            try:
                datetime_str = str([c for c in dl][1].contents[0].contents[0]).split(', ')[1]
            except Exception as ex:
                try:
                    datetime_str = str([c for c in dl][1].contents[0].split(', ')[1])
                except Exception as ex:
                    def prep_when_field(field):
                        return str(soup.find('span', attrs={'class': field}).contents[0]).replace(',', '').strip()
                    month = prep_when_field('m-date__month') # 'Jan'
                    day = prep_when_field('m-date__day')
                    year = prep_when_field('m-date__year')
                    time_str = prep_when_field('time') # 8:30 pm
                    datetime_str = f'{month} {day} {year} {time_str}' # 'Jan 25 2020 7:30 pm'
                    start_dt = dt.datetime.strptime(datetime_str, '%b %d %Y %I:%M %p')
            if start_dt is None:
                start_dt = dt.datetime.strptime(datetime_str, '%m/%d/%y @ %I:%M%p')
            if dl and len(dl.find_all('dt')) > 1:
                recurring = True

        set_start_end_fields_from_start_dt(csv_dict, start_dt)

        #----------------------------------------------------------------
        # Venue
        event_venue = 'New Jersey Performing Arts Center'
        csv_dict['venue_name'] = event_venue
        title_venue = 'NJPAC'
        csv_dict['event_name'] = f'{event_name}, at {title_venue}'

        #----------------------------------------------------------------
        # Description
        #
        contents_div = soup.find('div', attrs={'class': 'event-single-content'})
        try:
            full_event_text = ''.join([str(p) for p in contents_div.find_all('p')])
        except Exception as ex:
            full_event_text = ''.join([str(p) for p in soup.find('div', attrs={'class': 'event_description'}).contents])
        csv_dict['event_description'] = full_event_text

        # Price
        # '$20 - $90'
        try:
            price_str = str([s for s in soup.find_all('span') if '$' in str(s)][0].contents[0])
        except Exception as ex:
            # Maybe the event is free
            if [s for s in soup.find_all('span') if 'FREE' in str(s)]:
                price = 0
        else:
            price_str = re.sub('[$ ]', '', price_str)
            csv_dict['event_cost'] = price_str

        # Tags
        set_tags_from_dict(csv_dict, event_tags)
        if recurring:
            csv_dict['event_tags'] += f',Recurring'

        # Image URL
        image_url = soup.find('meta', attrs={'property': 'og:image'})['content']
        csv_dict['external_image_url'] = image_url

        return csv_dict
