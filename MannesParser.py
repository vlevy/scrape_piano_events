import datetime as dt
import json
import re
import urllib
from EventParser import EventParser
from parser_common_code import utc_to_local, is_pianyc_related, is_pianyc_related_as_accompanied, \
    set_start_end_fields_from_start_dt, initialize_csv_dict, set_tags_from_dict

# Map venues in the listing to the exact venue name in PIANYC
venue_map = {
    '': 'Arnhold Hall at the New School',
    '1127 6th Ave, New York, NY 10036': 'Steinway Hall',
    'Alice Tully Hall, Lincoln Center': 'Alice Tully Hall at Lincoln Center',
    'Alice Tully Hall at Lincoln Center': 'Alice Tully Hall at Lincoln Center',
    'Albert and Vera List Academic Center': 'The New School, Albert and Vera List Academic Center',
    'Anna-Maria and Stephen Kellen Gallery, Sheila C. Johnson Design Center': 'Anna-Maria and Stephen Kellen Gallery at Parsons School of Design',
    'Baisley Powell Elebash Recital Hall, Arnold Hall': 'Arnhold Hall at the New School',
    'Bohemian National Hall': 'Bohemian National Hall',
    'Consulate General of Poland': 'Consulate General of Poland',
    'Consulate of the Federal Republic of Germany': 'Consulate General of Germany',
    'Eugene Lang College of Liberal Arts at The New School': 'Eugene Lang College of Liberal Arts at The New School',
    'Gerald W. Lynch Theater at John Jay College': 'Gerald W. Lynch Theater at John Jay College',
    'Gerald W. Lynch Theater': 'Gerald W. Lynch Theater at John Jay College',
    'Gerald W Lynch Theater': 'Gerald W. Lynch Theater at John Jay College',
    'German Consulate General, New York': 'Consulate General of Germany',
    'House of the Redeemer': 'House of the Redeemer',
    'Klein Conference Room, Room A510, Alvin Johnson/J.M. Kaplan Hall': 'Alvin Johnson/J.M. Kaplan Hall',
    'Madison Avenue Presbyterian Church': 'Madison Avenue Presbyterian Church',
    'Saint Jean Baptiste Church': 'St. Jean Baptiste Church',
    'Sky Room, 12th floor': 'Arnhold Hall at the New School',
    'Steinway': 'Steinway Hall',
    'Steinway Hall': 'Steinway Hall',
    'The Auditorium, Alvin Johnson/J.M. Kaplan Hall': 'Alvin Johnson/J.M. Kaplan Hall',
    'The Auditorium, Room A106, Alvin Johnson/J.M. Kaplan Hall': 'Alvin Johnson/J.M. Kaplan Hall',
    'The Grolier Club': 'The Grolier Club',
    'The Union Club': 'The Union Club',
    'Theresa Lang Community and Student Center, Arnhold Hall': 'Arnhold Hall at the New School',
    'Union Square Park - North Plaza, NYC': 'Union Square',
    'University Center': 'The New School University Center',
    'Weill Recital Hall at Carnegie Hall': 'Carnegie Hall',
    'Wollman Hall, Eugene Lang College': 'Eugene Lang College of Liberal Arts at The New School',
}
# Map venues in PIANYC to what to put in the post title, e.g., "Richard Goode Master Class, at Mannes"
venue_title_map = {
    'Alvin Johnson/J.M. Kaplan Hall': 'The New School',
    'Parsons School of Design': 'The New School',
    'Anna-Maria and Stephen Kellen Gallery at Parsons School of Design': 'The New School',
    'Arnhold Hall at the New School': 'The New School',
    'Bohemian National Hall': 'the Bohemian National Hall',
    'Consulate General of Germany': 'Consulate General of Germany',
    'Consulate General of Poland': 'Consulate General of Poland',
    'Eugene Lang College of Liberal Arts at The New School': 'The New School',
    'Glass Box Performance Space at the New School': 'The New School',
    'House of the Redeemer': 'House of the Redeemer',
    'John L. Tishman Auditorium, University Center': 'The New School',
    'Alice Tully Hall at Lincoln Center': 'Lincoln Center',
    'Madison Avenue Presbyterian Church': 'Madison Avenue Presbyterian Church',
    'St. Jean Baptiste Church': 'St. Jean Baptiste Church',
    'Carnegie Hall': 'Carnegie Hall',
    'Steinway Hall': 'Steinway Hall',
    'Union Square': 'Union Square',
    'The Grolier Club': 'The Grolier Club',
    'The New School': 'The New School',
    'The Union Club': 'The Union Club',
    'The New School University Center': 'The New School',
    'The New School, Albert and Vera List Academic Center': 'The New School',
    'Gerald W. Lynch Theater at John Jay College': 'John Jay College',
}


class MannesParser(EventParser):

    def parse_soup_to_event(self, url, soup):
        csv_dict = initialize_csv_dict(url)
        csv_dict['organizer_name'] = 'Mannes College of Music'
        event_tags = ['Classical', 'Mannes']

        # Pull out the Google event information
        try:
            google_cal = soup.find('a', attrs={'class': 'fa-google'})['href']
            google_cal = urllib.parse.unquote(google_cal)
            google_cal_dict = dict([(p.split('=')[0], (p.split('=')[1])) for p in google_cal.split('&')
                                    if len(p.split('=')) == 2][1:])
        except Exception as ex1:
            # Google Event Annotation
            try:
                json_text = soup.find('script', attrs={'type': 'application/ld+json'}).contents[0]
                google_cal_dict = json.loads(json_text)
            except Exception as ex2:
                print('No Google event annotation found, skipping event.')
                return None

        # Venue
        try:
            venue_name = google_cal_dict['location'].replace('+', ' ').strip()
        except Exception as ex:
            venue_name = google_cal_dict['location']['name']

        if  'arnhold' in venue_name.lower() or 'stiefel' in venue_name.lower():
            venue_name = 'Arnhold Hall at the New School'
        elif 'tishman' in venue_name.lower():
            venue_name = 'John L. Tishman Auditorium, University Center'
        elif 'glassbox' in venue_name.lower() or 'glass box' in venue_name.lower():
            venue_name = 'Glass Box Performance Space at the New School'

        location_venue = venue_map.get(venue_name, None) or venue_title_map[venue_name]
        try:
            title_venue = venue_title_map[location_venue]
        except Exception as ex:
            raise
        csv_dict['venue_name'] = location_venue

        # Event name
        try:
            event_name = str(soup.find('title').contents[0])
        except Exception as ex:
            google_cal_dict['name']

        csv_dict['event_name'] = f'{event_name}, at {title_venue}'

        # Date and time: '20191117T190000Z/20191117T213000Z'
        try:
            google_calendar_href = soup.find('a', attrs={'class': 'tns_events_cta'})['href']

            date_index = google_calendar_href.find('dates=') + 6
            utc_dates_string = google_calendar_href[date_index: date_index + 33]
            if utc_dates_string[16] == '/':
                # Both start and end dates, e.g., '20191117T190000Z/20191117T213000Z'
                utc_dates = utc_dates_string.split('/')
                try:
                    start_dt = utc_to_local(dt.datetime.strptime(utc_dates[0], '%Y%m%dT%H%M%SZ'))
                    end_dt   = utc_to_local(dt.datetime.strptime(utc_dates[1], '%Y%m%dT%H%M%SZ'))
                except Exception as ex:
                    raise
            else:
                # Single start date, e.g., '20190916T233000Z'
                start_dt = utc_to_local(dt.datetime.strptime(utc_dates_string[0:16], '%Y%m%dT%H%M%SZ'))
                end_dt = None
        except Exception as ex:
            start_string = google_cal_dict['startDate']
            end_string = google_cal_dict['endDate']
            start_dt = dt.datetime.strptime(start_string[:-6], '%Y-%m-%dT%H:%M:%S')
            end_dt = dt.datetime.strptime(end_string[:-6], '%Y-%m-%dT%H:%M:%S')

        set_start_end_fields_from_start_dt(csv_dict, start_dt, end_dt)

        # Event description
        try:
            paragraphs = [str(p) for p in soup.find('div', attrs={'class': ('vht')})]
            description = ''.join(paragraphs)
        except Exception as ex:
            description = google_cal_dict['description']

        csv_dict['event_description'] = description

        # Relevant
        relevant = is_pianyc_related(str(description)) or \
                   is_pianyc_related_as_accompanied(str(description))
        csv_dict['relevant'] = relevant

        # Price
        try:
            json_script = str([s.contents[0] for s in soup.find_all('script')
                               if s.contents and s.contents[0].find('ticket_cost:') >= 0][0])
            cost_string = re.search('\"(.+?)\"', json_script[json_script.find('ticket_cost'):]).groups()[0]
            sorted_prices = sorted([int(p.replace('$', '')) for p in re.findall('\$\d+', cost_string)])
            if 'free' in cost_string.lower():
                sorted_prices.insert(0, 0)
                sorted_prices = list(set(sorted_prices))
            if len(sorted_prices) == 1:
                price_string = f'{sorted_prices[0]}'
            elif len(sorted_prices) > 1:
                price_string = f'{sorted_prices[0]}-{sorted_prices[-1]}'
            else:
                price_string = ''
        except Exception as ex:
            print('No cost found')
            # Assume it's free
            price_string = '0'

        csv_dict['event_cost'] = price_string

        # Tags
        if 'stone at the new school' in (event_name + description).lower():
            # These are not student performances
            event_tags.append('Avant-Garde')
            event_tags.append('Contemporary')
        else:
            event_tags += ['Student Recital']

        set_tags_from_dict(csv_dict, event_tags)

        # Image URL
        try:
            image_url = str(soup.find('meta', attrs={'name': 'og:image'})['content'])
        except Exception as ex:
            style = str(soup.find('div', attrs={'class': 'set-as-event-image'})['style'])
            image_url = re.search("background-image:url\('(.+)'", style).groups()[0]
            if image_url.startswith('//'):
                image_url = f'https:{image_url}'

        csv_dict['external_image_url'] = image_url

        return csv_dict
