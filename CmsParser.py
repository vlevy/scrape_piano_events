from datetime import datetime
import re
from EventParser import EventParser
from parser_common_code import initialize_csv_dict, set_start_end_fields_from_start_dt, parse_event_tags

VENUE_TRANSLATIONS_FOR_VENUE = {
    '': 'Lincoln Center',
    'Alice Tully Hall': 'Alice Tully Hall at Lincoln Center',
    'David Geffen Hall': 'David Geffen Hall at Lincoln Center',
    'Kaplan Penthouse': 'Stanley H. Kaplan Penthouse at Lincoln Center',
    'Rosemary and Meredith Willson Theater': 'Rosemary and Meredith Willson Theater at Juilliard School',
    'Daniel and Joanna S. Rose Studio': 'Daniel and Joanna S. Rose Studio at Lincoln Center',
    'Rose Studio': 'Daniel and Joanna S. Rose Studio at Lincoln Center',
}


class CmsParser(EventParser):
    """Parser for the Chamber Music Society of Lincoln Center
    """
    @staticmethod
    def read_urls():
        """Read the event-page URLs for the first 10 pages of piano events in Manhattan
        """
        with open('chamber_music_society_urls_spring_2018.txt', encoding='utf-8') as url_file:
            urls = url_file.readlines()

        return urls


    def parse_image_url(self, soup) -> str:
        try:
            # https://res.cloudinary.com/cmslc/image/upload/c_fill,f_auto,g_auto,h_320,q_auto,w_480/v1/Radio/19-20%20Programs/102818_Juho_Pohjonen.jpg
            image_url = str(soup.find('picture', attrs={'class': 'production-image__media'}).find('source')['srcset'])
            image_file_name = re.search('[a-zA-z0-9_]+\.jpg', image_url).group()
            folder = 'CMS'
        except Exception as ex:
            image_url = 'CMS_default.jpg'
            folder = None
            image_file_name = None
            # print('No image URL found in {0}'.format(url))

        return folder, image_file_name, image_url

    @staticmethod
    def parse_soup_to_event(url, soup):
        """Parses a soup object into a dictionary whose keys are the CSV rows
        required by the imported CSV
        """

        # -----------------------------------
        # Easy fields
        # -----------------------------------
        csv_dict = initialize_csv_dict(url)

        # Venue
        try:
            venue = str(soup.find('div', attrs={'class': 'aside__body s-prose'}).find('p').contents[1].contents[0])
        except Exception as ex:
            print('Unable to find venue. CHECK MANUALLY')
        else:
            if venue.endswith('.'):
                venue = venue[:-1]
            csv_dict['venue_name'] = VENUE_TRANSLATIONS_FOR_VENUE[venue]

        # Organizer
        csv_dict['organizer_name'] = 'Chamber Music Society of Lincoln Center'

        # When
        # 'Tuesday, May 7, 2019, 7:30 PM'
        event_when = soup.find('div', attrs={'class': 'production-header__date-description'}).contents[0].split('\n')[1].strip()
        try:
            # 'Tuesday, May 7, 2019, 7 PM'
            event_dt = datetime.strptime(event_when, '%A, %B %d, %Y, %I %p')
        except Exception as ex:
            # 'Tuesday, May 7, 2019, 7:30 PM'
            try:
                event_dt = datetime.strptime(event_when, '%A, %B %d, %Y, %I:%M %p')
            except Exception as ex:
                try:
                    # 'Thursday, May 31, 11:00 AM'
                    event_dt = datetime.strptime(event_when, '%A, %B %d, %I:%M %p')
                    event_dt = event_dt.replace(year=datetime.today().year)
                except Exception as ex:
                    try:
                        # 'Thursday, February 24, 2022 7:30 PM'
                        event_dt = datetime.strptime(event_when, '%A, %B %d, %Y %I:%M %p')
                    except Exception as ex:
                        try:
                            # March, 7, 2022, 11:00 AM
                            event_dt = datetime.strptime(event_when, '%B, %d, %Y, %I:%M %p')
                        except Exception as ex:
                            print('Unable to parse date: {0}'.format(event_when))
        # print('Parsed '{0}' to {1}'.format(event_dt.strip(), dt))
        set_start_end_fields_from_start_dt(csv_dict, event_dt, minutes=90)

        # $<span class="u-large">40</span>.00–$<span class="u-large">80</span>.00
        try:
            event_costs = [eval(s.contents[0]) for s in soup.find('div', attrs={'class': 'production-header__price'}).find_all('span', attrs={'class': 'u-large'})]
        except Exception as ex:
            event_costs = [0]
        try:
            csv_dict['event_cost'] = '-'.join(['{0}'.format(c) for c in event_costs])
        except Exception as ex:
            raise
        csv_dict['event_website'] = url
        csv_dict['external_image_url'] = soup.find_all('source')[0].attrs['srcset']

        #--------------------------------------
        # Body

        # Description
        if soup.find('div', attrs={'class': 'production-content__details'}).contents == ['\n']:
            print('WARNING: No description found')
            return None
        description = [str(soup.find('div', attrs={'class': 'production-content__details'}).contents[1].contents[0])]
        description.append('')

        # Program
        program_section = soup.find('div', attrs={'class': 'production-content__details'}).contents[1]
        program_items = program_section.find_all('li')
        program_lines = list()
        for item in program_items:
            composer = str(item.contents[3])
            """
item.contents
Out[3]: 
['\n',
 <span class="production-program__audio-icon"><svg aria-hidden="true" class="o-icon icon-play o-icon--small">
 <use xlink:href="#icon-play" xmlns:xlink="http://www.w3.org/1999/xlink"></use>
 </svg>
 </span>,
 '\n',
 <strong>Timo Andres</strong>,
 '\n                    Quintet for Piano, Two Violins, Viola, and Cello (2012)\n                ']

"""
            work = ' '.join([str(c).strip() for c in item.contents if not any(('svg>' in str(c),'<span' in str(c), not len(str(c).strip()), composer in str(c).strip()))])
            this_line = '{0} {1}'.format(composer, work)
            program_lines.append(this_line)

        if program_lines:
            description.append('')
            description.append('<strong>Program</strong>')
            for p in program_lines:
                description.append(p)

        # Performers
        pianists = []
        performer_items = soup.find_all('div', attrs={'class': 'artist-item__body'})
        if performer_items:
            description.append('')
            if len(performer_items) == 1:
                description.append('<strong>Performer</strong>')
            else:
                description.append('<strong>Performers</strong>')

            for performer_item in performer_items:
                performer = performer_item.find('h3', attrs={'class': 'artist-item__title'}).contents[0]
                if performer_item.find('span', attrs={'class': 'artist-item__instrument'}).contents:
                    instrument = performer_item.find('span', attrs={'class': 'artist-item__instrument'}).contents[0]
                elif performer_item.find('span', attrs={'class': 'artist-item__role'}).contents:
                    instrument = performer_item.find('span', attrs={'class': 'artist-item__role'}).contents[0]
                else:
                    instrument =  None

                if performer and instrument:
                    performer_line = f'{performer}, {instrument}'
                elif performer:
                    performer_line = f'{performer}'
                description.append(performer_line)

        csv_dict['event_description'] = '\n'.join(description)
        #
        #--------------------------------------

        # Name
        name_from_page = soup.find('h2', attrs={'class': 'production-header__title'}).contents[0]
        event_name = 'Chamber Music Society of Lincoln Center, {0}'.format(name_from_page)
        if False and pianists:
            # Call out the pianists
            event_name = '{0}; {1}, Piano'.format(event_name, ' and '.join(pianists))
        csv_dict['event_name'] = event_name

        # Tags
        tags = ['Classical', 'Ensemble', 'Chamber Music']
        if event_costs == [0]:
            tags.append('Free')
        parse_event_tags(csv_dict, tags, csv_dict['event_description'])
        csv_dict['event_tags'] = ','.join(tags)

        return csv_dict
