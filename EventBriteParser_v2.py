import re
from datetime import datetime
import json
from parser_common_code import parse_url_to_soup, encode_html, initialize_csv_dict, set_start_end_fields_from_start_dt, \
    parse_price_range, set_tags_from_dict
from EventParser import EventParser

class EventBriteParser_v2(EventParser):

    VENUES = {

    }

    @staticmethod
    def read_urls(url_file_name):
        """Read the event-page URLs for the first 10 pages of piano events in Manhattan
        """
        urls = []
        for page in range(10):
            url = f'https://www.eventbrite.com/d/ny--manhattan/piano/?loc=Manhattan%2C+New+York%2C+NY%2C+USA&page={page + 1}&q=piano'
            print('Reading URL {0}'.format(url))
            soup = parse_url_to_soup(url)
            events_json_str = [l for l in str(soup).splitlines() if 'window.__SERVER_DATA__' in l][0].strip()
            events_json = re.search('(?P<json>\{.+\})', events_json_str).group('json')
            events = json.loads(events_json)
            for event in events['search_data']['events']['results']:
                url = event.get('url', event.get('tickets_url'))
                # Skip events at Pianos, 158 Ludlow Street
                if ('primary_venue' in event and
                        'address' in event['primary_venue'] and
                        'address_1' in event['primary_venue']['address'] and
                        event['primary_venue']['address']['address_1'] == '158 Ludlow Street'):
                    continue
                urls.append(url)

        # Write the URLs out to a file for safekeeping
        with open(url_file_name, 'w', newline='\n') as url_file:
            for url in urls:
                url_file.write(url + '\n')

        return urls

    @staticmethod
    def parse_soup_to_event(url, soup):
        """Parses a soup object into a dictionary whose keys are the CSV rows
        required by the imported CSV
        """

        csv_dict = initialize_csv_dict(url)

        # Details are stored in a JSON element
        try:
            event_json = soup.find_all('script', attrs={'type': 'application/ld+json'})[0].contents[0]
            # Some events have improperly encoded newlines
            event_json = event_json.replace('\t', ' ')
            event_details = json.loads(event_json)
        except Exception as ex:
            print('Unable to parse event-details JSON in {0}: {1}'.format(url, ex))
            return None

        tags_list = ['EB']
        # "2018-03-25T17:00:00-04:00"
        try:
            start_dt = datetime.strptime(event_details['startDate'][:19], '%Y-%m-%dT%H:%M:%S')
            end_dt   = datetime.strptime(event_details['endDate'][:19], '%Y-%m-%dT%H:%M:%S')
            set_start_end_fields_from_start_dt(csv_dict, start_dt, end_dt)
        except KeyError as ex:
            print('Start date not found')

        try:
            csv_dict['event_name'] = '{0} at {1}'.format(event_details['name'], event_details['location']['name'])
        except KeyError as ex:
            print('Event name not found. Skipping.')
            return None

        venue = str(event_details['location']['name']).strip()
        csv_dict['venue_name'] = venue
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
        try:
            description = '\n'.join(str(c) for c in soup.find('div', attrs={'class': 'eds-text--left'}).contents)
        except Exception as ex:
            summary = f"<strong>{event_details['description']}</strong>"
            description_paragraphs = [summary, '']
            description_paragraph_sections = soup.find_all('div', attrs={'class': 'structured-content-rich-text'})
            if description_paragraph_sections:
                for section in description_paragraph_sections:
                    for i, p in enumerate(section.find_all('p')):
                        if p.contents:
                            description_paragraphs.append(''.join([str(c) for c in p.contents]))
                        else:
                            description_paragraphs += ''
            else:
                print('Warning: Only event summary available')
            description = f"<p>{'</p><p>'.join(description_paragraphs)}</p>"

        csv_dict['event_description'] = description

        if 'organizer' in event_details and 'event_description' in event_details['organizer']:
            csv_dict['event_description'] += '\r\n' + encode_html(event_details['organizer']['description'])
        set_tags_from_dict(csv_dict, tags_list)
        if free:
            csv_dict['event_tags'] = ','.join((csv_dict['event_tags'], 'Free'))

        if 'image' in event_details:
            csv_dict['external_image_url'] =  event_details['image']
        else:
            print('No image URL in {0}'.format(url))

        # Filters
        if 'upstairs lounge' in csv_dict['event_name'].lower():
            return None
        if 'dueling pianos' in csv_dict['event_name'].lower():
            return None
        if 'pianos showroom' in csv_dict['event_name'].lower():
            return None

        if not EventBriteParser_v2.VENUES.get(venue, None):
            print(f'Missing venue "{venue}"')

        return csv_dict
