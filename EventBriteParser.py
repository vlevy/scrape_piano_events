import json
import os.path
from datetime import datetime
from parser_common_code import parse_url_to_soup, parse_file_to_soup, soup_to_str, encode_html, \
    set_start_end_fields_from_start_dt, initialize_csv_dict, parse_price_range
from EventParser import EventParser

LIVE_READ = True

class EventBriteParser(EventParser):

    @staticmethod
    def read_urls():
        """Read the event-page URLs for the first 10 pages of piano events in Manhattan
        """
        urls = []
        for page in range(10):
            url_file_name = 'EventBrite_Page_{0:02d}'.format(page + 1)

            if LIVE_READ:
                url = f'https://www.eventbrite.com/d/ny--manhattan/piano/?loc=Manhattan%2C+New+York%2C+NY%2C+USA&page={page + 1}&q=piano'
                print('Reading URL {0}'.format(url))
                soup = parse_url_to_soup(url)
                with open(url_file_name, 'w', encoding='utf-8') as url_page_file:
                    url_page_file.write(soup_to_str(soup) + '\n')
            else:
                print('Reading file {0}'.format(url_file_name))
                soup = parse_file_to_soup(os.path.abspath(url_file_name))

            url_elements = soup.find_all('div', attrs={'class': 'list-card-v2'})
            for element in url_elements:
                url = element['data-share-url'].replace('?aff=es2', '')
                urls.append(url)

        # Write the URLs out to a file for safekeeping
        with open('EventBrite_URLs.txt', 'w', newline='\n') as url_file:
            for url in urls:
                url_file.write(url + '\n')

        return urls

    @staticmethod
    def parse_soup_to_event(url, soup):
        """Parses a soup object into a dictionary whose keys are the CSV rows
        required by the imported CSV
        """
        csv_dict = initialize_csv_dict()

        # Details are stored in a JSON element
        try:
            event_json = soup.find_all('script', attrs={'type': 'application/ld+json'})[0].contents[0]
            # Some events have improperly encoded newlines
            event_json = event_json.replace('\t', ' ')
            event_details = json.loads(event_json)
        except Exception as ex:
            print('Unable to parse event-details JSON in {0}: {1}'.format(url, ex))
            return None

        # "2018-03-25T17:00:00-04:00"
        start_dt = datetime.strptime(event_details['startDate'][:19], '%Y-%m-%dT%H:%M:%S')
        end_dt   = datetime.strptime(event_details['endDate'][:19], '%Y-%m-%dT%H:%M:%S')
        set_start_end_fields_from_start_dt(csv_dict, start_dt, end_dt)

        csv_dict['event_name'] = '{0} at {1}'.format(event_details['name'], event_details['location']['name'])
        csv_dict['venue_name'] = event_details['location']['name']
        csv_dict['organizer_name'] = event_details['organizer']['name']

        # Price
        free = False
        if 'offers' in event_details:
            low = high = None
            if 'lowPrice' in event_details['offers'][0] and \
                    'highPrice' in event_details['offers'][0]:
                low = event_details['offers'][0]['lowPrice']
                high = event_details['offers'][0]['highPrice']
            elif 'price' in event_details['offers'][0]:
                low = high = event_details['offers'][0]['price']

            if low is not None:
                if low == high:
                    csv_dict['event_cost'] = parse_price_range('${0}'.format(low))
                else:
                    csv_dict['event_cost'] = parse_price_range('${0}-${1}'.format(low, high))
                if low == 0:
                    free = True

        csv_dict['event_phone'] = None
        csv_dict['event_website'] = url
        csv_dict['show_map_link'] = False
        csv_dict['show_map'] = True

        # Event description
        event_description = encode_html(event_details['description'])
        csv_dict['event_description'] = event_description

        if 'organizer' in event_details and 'event_description' in event_details['organizer']:
            csv_dict['event_description'] += '\r\n' + encode_html(event_details['organizer']['description'])
        set_tags_from_dict(csv_dict)
        if free:
            csv_dict['event_tags'] = ','.join((csv_dict['event_tags'], 'Free'))

        if 'image' in event_details:
            csv_dict['external_image_url'] =  event_details['image']
        else:
            print('No image URL in {0}'.format(url))

        return csv_dict
