import datetime as dt
import re

from EventParser import EventParser

class SymphonySpaceParser(EventParser):
    """
    Symphony Space pparser.
    """
    def parse_soup_to_event(self, url, soup):
        csv_dict = { \
            'categories': LIVE_PERFORMANCE,
            'show_map': 'TRUE',
            'show_map_link': 'FALSE',
            'event_website': url,
        }
        event_tags = set()

        # Venue
        venue = 'Symphony Space'
        csv_dict['venue_name'] = venue

        # Event name
        title = str(soup.find('meta', attrs={'property': 'og:title'})['content'])
        csv_dict['event_name'] = f'{title}, at {venue}'

        # Contents
        try:
            description = ''.join([str(p) for p in soup.find('div', attrs={'class': 'entry-full-description'}).contents])
        except Exception as ex:
            description = ''.join([str(p) for p in soup.find('div', attrs={'class': 'event-entry-short-description'}).contents])
        csv_dict['event_description'] = description

        # Price
        price_tags = soup.find_all('span', attrs={'class': 'event-price-range-row'})
        if price_tags and price_tags[0].contents:
            prices = sorted(
                set([int(p) for p in re.findall('\$([0-9]+)', ' '.join([str(p.contents[0]) for p in price_tags if p.contents]))]))
            if len(prices) > 1:
                price_str = f'{prices[0]}-{prices[-1]}'
            elif len(prices) == 1:
                price_str = f'{prices[0]}'
            else:
                price_str = ''
                print('Unable to find price')
            if price_str:
                csv_dict['event_cost'] = price_str

        # When '2020-01-11T21:00:00-05:00'
        start_dt = None
        if not start_dt:
            try:
                start_str = str(soup.find('time')['datetime'])[:19]
                start_dt = dt.datetime.strptime(start_str, '%Y-%m-%dT%H:%M:%S')
            except Exception as ex:
                pass
        if not start_dt:
            try:
                # 'Mon, Oct 14, 2019 | 8pm'
                date_rows = soup.find_all('span', attrs={'class': 'event-dates-row'})
                datetime_str = [str(c.contents[0]).strip() for c in date_rows][0][5:]
                try:
                    # 'Oct 14, 2019 | 8pm'
                    start_dt = dt.datetime.strptime(datetime_str, '%b %d, %Y | %I%p')
                except Exception as ex:
                    # 'Oct 14, 2019 | 8:30pm'
                    start_dt = dt.datetime.strptime(datetime_str, '%b %d, %Y | %I:%M%p')

                if len(date_rows) > 1:
                    print('RECURRING EVENT -- CHECK RECURRANCES MANUALLY')
                    event_tags.add('recurring')
            except Exception as ex:
                pass

        if not start_dt:
            print('Unable to parse date/time')
            return None

        set_start_end_fields_from_start_dt(csv_dict, start_dt)

        # Image
        try:
            image_url = str(soup.find('img', attrs={'class': 'center-block'})['src']).split('.jpg')[0] + '.jpg'
        except Exception as ex:
            print('No image found - using default')
            image_url = 'https://symphonyspace.s3.amazonaws.com/images/featured-sections/Getting-Here-Patch-Image.jpg'
        csv_dict['external_image_url'] = image_url

        # Tags
        set_tags_from_dict(csv_dict, event_tags)

        return csv_dict
