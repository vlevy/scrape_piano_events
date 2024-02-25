import datetime as dt
import re
from pathlib import PurePath

from EventParser import EventParser
from parser_common_code import (
    any_match,
    get_full_image_path,
    initialize_csv_dict,
    is_relevant_to_site,
    is_relevant_to_site_as_accompanied,
    parse_event_tags,
    parse_price_range,
    set_start_end_fields_from_start_dt,
)

DEFAULT_JUILLIARD_IMAGE_URL = 'https://www.juilliard.edu/sites/default/files/styles/wide_1920x1080/public/juilliard37_2400x1350.jpg'

# Venue translations. 'None' means use the name is unchanged from the key.
VENUE_TRANSLATIONS = {
    '': 'the Juilliard School',
    'Abyssinian Baptist Church': None,
    'Alice Tully Hall': 'Lincoln Center',
    'Blue Note Jazz Club': 'skip',
    'Bruno Walter Auditorium at NYPL for the Performing Arts':  'Bruno Walter Auditorium',
    'Carnegie Hall': None,
    'Cathedral of St. John the Divine': None,
    'The Cathedral Church of St. John the Divine': 'Cathedral of St. John the Divine',
    'Chelsea Factory': None,
    "Christ and St. Stephen's Church": "Christ & St. Stephen's Episcopal Church",
    'Corpus Christi Church': None,
    'Damrosch Park': 'skip',
    'David Geffen Hall': 'Lincoln Center',
    'Daniel and Joanna S. Rose Studio': 'Lincoln Center',
    'Dizzy\'s Club Coca-Cola': None,
    'Dizzy\'s Club': 'Dizzy\'s Club Coca-Cola',
    'Glorya Kaufman Dance Studio': 'the Juilliard School',
    'Holy Trinity Lutheran Church': None,
    'Kaufman Dance Studio': 'the Juilliard School',
    'Lippes Concert Hall in Slee Hall, SUNY': 'skip',
    'Livestream': 'skip',
    'Madison Avenue Presbyterian Church': None,
    'Marble Collegiate Church': None,
    'Mary Seaton Room at Kleinhans Music Hall': 'skip',
    'Merkin Hall': 'Merkin Concert Hall at Kaufman Music Center',
    'Morse Hall': 'the Juilliard School',
    'Morse Recital Hall': 'Morse Hall',
    'National Sawdust': 'skip',
    'Paul Hall': 'the Juilliard School',
    'Peter Jay Sharp Theater': 'the Juilliard School',
    'Rm 305': 'the Juilliard School',
    'Rm 305 - Ellen and James S. Marcus Vocal Arts Studio': 'the Juilliard School',
    'Room 305 - Ellen and James Marcus Vocal Arts Studio': 'the Juilliard School',
    'Rm 309 - Bruno Walter Orchestral Studio': 'the Juilliard School',
    'Rm 340 - Jazz Studio': 'the Juilliard School',
    'Rm 543 - Harris/Woolfson Orchestral Studio': 'the Juilliard School',
    'Rosemary and Meredith Willson Theater': 'the Juilliard School',
    'Saint Michael’s Church': 'St. Michael’s Church',
    'Saint Thomas Church': "Saint Thomas Church Fifth Avenue",
    'Streaming Event': None,
    'St. Bartholomew\'s Episcopal Church': 'St. Barts Park Avenue',
    'Stephanie P. McClelland Drama Theater': 'the Juilliard School',
    'Stephanie P. McClelland Theater': 'the Juilliard School',
    'The Bruno Walter Auditorium':  'Bruno Walter Auditorium',
    'The Charles Engelhard Court at The Metropolitan Museum of Art': 'Metropolitan Museum of Art',
    'The Morgan Library & Museum': 'The Morgan Library and Museum',
    'The Church of Saint Mary the Virgin': 'The Church of Saint Mary the Virgin',
    'Venue Display Name': 'the Juilliard School',
    'Weill Recital Hall': 'Carnegie Hall',
    'Weill Recital Hall at Carnegie Hall': 'Carnegie Hall',
    'Woolsey Hall at Yale University': 'skip',
}


class JuilliardParser(EventParser):

    def parse_image_url(self, soup) -> str:
        try:
            # https://www.juilliard.edu/sites/default/files/styles/wide_640x360/public/events/20180925_JazzKenya_113_EDITED_1.jpg?itok=Thc7xiYw
            image_url_suffix = soup.find('div', attrs={'class': 'field--name-field-image'}).find('img').attrs['src']
            image_url = f'https://www.juilliard.edu{image_url_suffix}'
            # Examples: 'https://www.juilliard.edu/sites/default/files/styles/wide_640x360/public/events/image.png?itok=eYF57vEs'
            # Parses to ('image', 'png', 'eYF57vEs')
            # https://www.juilliard.edu/sites/default/files/styles/wide_event_1270x715_with_focal_point/public/events/jsq_rotator_2400x1350_a1_1.jpeg?h=d1cb525d&itok=lOxJPJde
            # Parses to ('image', 'png', 'eYF57vEs')
            stem, ext, token = re.search('([a-zA-Z0-9_]+)\.(JPG|JPEG|PNG|jpg|jpeg|png)\?itok=(.{8})', image_url).groups()
            image_file_name = f'{stem}_{token}.{ext}'
            folder = 'Juilliard'
        except Exception as ex:
            image_url = DEFAULT_JUILLIARD_IMAGE_URL
            folder = None
            image_file_name = None
            # print('No image URL found in {0}'.format(url))

        return folder, image_file_name, image_url

    def parse_soup_to_event(self, url, soup):
        """Parses a soup object into a dictionary whose keys are the CSV rows
        required by the imported CSV
        """

        # -----------------------------------
        # Easy fields
        # -----------------------------------
        csv_dict = initialize_csv_dict(url)
        csv_dict['organizer_name'] = 'Juilliard School'

        # -----------------------------------
        # Event name
        # -----------------------------------
        try:
            event_name_from_page = str(soup.find('h1', attrs={'class': 'event-hero-banner__title'}).find('span').contents[0])
        except Exception as ex:
            print(f'Skipping {url} because event name was not found')
            return None

        # -----------------------------------
        # Venue
        # -----------------------------------
        venue_element = soup.find('div', attrs={'class': 'field--name-name field__item'})
        if venue_element:
            venue_from_page = venue_element.contents[0].strip()
        else:
            venue_from_page = ''
        venue = VENUE_TRANSLATIONS[venue_from_page] or venue_from_page
        if venue == 'skip':
            print(f'Skipping event at "{venue_from_page}"')
            return None
        if venue.startswith('the '):
            # Strip off leading 'the'
            venue = venue[4:]

        assert(venue)
        csv_dict['venue_name'] = venue

        # -----------------------------------
        # Event date/time
        # -----------------------------------

        # Date/time example: '2019-09-19 19:30:00'
        try:
            when_start = str(soup.find('var', attrs={'class': 'atc_date_start'}).contents[0]).strip()
            event_dt = dt.datetime.strptime(when_start.strip(), '%Y-%m-%d %H:%M:%S')
            set_start_end_fields_from_start_dt(csv_dict, event_dt, minutes=90)
        except Exception as ex:
            print(f"Unable to parse event start time: {ex}")

        # -----------------------------------
        # Image URL
        # -----------------------------------
        image_folder, image_file_name, image_url = self.parse_image_url(soup)
        full_image_path = get_full_image_path(image_folder, image_file_name)
        image_file_name = PurePath(full_image_path).name
        csv_dict['external_image_url'] = image_file_name

        # -----------------------------------
        # Price
        # -----------------------------------
        price = None
        price_element = soup.find('div', attrs={'class': 'field--name-field-admission'})
        if price_element:
            admission = '\r\n'.join([str(line) for line in price_element.contents])
            admission_single_line = ' '.join([str(line) for line in price_element.contents])
            price = parse_price_range(admission_single_line)
        csv_dict['event_cost'] = price or 0

        # -----------------------------------
        # Event description
        # -----------------------------------
        relevant = is_relevant_to_site(event_name_from_page) or \
                   is_relevant_to_site_as_accompanied(event_name_from_page) or \
                   event_name_from_page == 'Pre-College Faculty Recital' or \
                   any_match(('MAP Student Recital', 'MAP Chamber', 'Chamber Music Recital',
                              'Honors Chamber Music', 'Ensemble Connect', 'Chamberfest', 'Vocal Arts'),
                             event_name_from_page)

        event_description_rows = [event_name_from_page, ]
        subtitle = soup.find('div', attrs={'class': 'field--name-field-subtitle'})
        if subtitle:
            event_description_rows.append('')
            event_description_rows += [p.contents[0] for p in subtitle.contents if str(p).strip()]
        program_list_element = soup.find('div', attrs={'class': 'field--name-field-program-information'})
        if program_list_element:
            program_list = program_list_element.contents
            relevant = relevant or \
                       is_relevant_to_site(str(program_list)) or \
                       is_relevant_to_site_as_accompanied(str(program_list))
            program = ''.join(str(work) for work in program_list)
            event_description_rows.append('')
            if not re.match('<em> *</em>', program):
                event_description_rows.append('')
                event_description_rows.append('<strong>Program</strong>')
                event_description_rows.append(program)

        if venue_from_page and ('Juilliard School' in venue):
            # If the event is being held at Juilliard, note the specific hall or room
            event_description_rows.append('')
            event_description_rows.append('<strong>Venue</strong>')
            event_description_rows.append(venue_from_page)

        if price:
            event_description_rows.append('')
            event_description_rows.append('<strong>Admission</strong>')
            event_description_rows.append(admission)
            event_description_rows.append('')

        description_html = '{0}\r\n'.format('\r\n'.join(event_description_rows))
        csv_dict['event_description'] = description_html
        is_precollege = 'pre-college' in description_html.lower()

        # -----------------------------------
        # Event tags
        # -----------------------------------
        event_tags = ['Juilliard', 'Classical']

        if any_match(('Faculty Recital',), (event_name_from_page, description_html)):
            event_tags.append('Faculty Recital')
        else:
            event_tags.append('Student Recital')

        if is_relevant_to_site(event_name_from_page):
            event_tags.append('Pure Keyboard')
            event_tags.append('Solo')
        else:
            event_tags.append('Ensemble')

        if is_precollege or 'Juilliard MAP Student Recital' in event_name_from_page:
            event_tags.append('Young Performer')

        # 'Michael Davidman and Jaeden Izik-Dzurko, Pianos | Bachauer Piano Recital at The Juilliard School'
        # parses to
        # 'Michael Davidman and Jaeden Izik-Dzurko, Pianos'
        event_name_from_page = event_name_from_page.split('|')[0].strip()

        # 'Brendon Elliott, Violin' parses to ('Brendon Elliott', ' Violin')
        match = re.match('(.+)\, *(.+$)', event_name_from_page)
        if match:
            student = match.groups()[0]
            instrument = match.groups()[1]
            if False:
                if instrument.lower().strip() == 'piano':
                    # Piano is implied
                    instrument = None
        else:
            student = None
            instrument = None
        if not csv_dict['event_cost']:
            event_tags.append('Free')

        event_text = ' '.join((event_name_from_page, description_html))
        parse_event_tags(csv_dict, event_tags, event_text)

        if False:
            # Forget about pre-college non-keyboard recitals
            if is_precollege and not is_relevant_to_site(event_name_from_page):
                print(f'Info: Non-keyboard pre-college event {event_name_from_page}')
                return None

        # Finalize some fields
        if student and instrument:
            if instrument.lower() == 'pianos':
                # Two pianos!
                csv_event_name = f'Juilliard Student Recital: {student}, {instrument}'
                event_tags += ['Ensemble', 'Four Hand', 'Pure Keyboard']
            elif relevant and instrument.lower() not in (
                'piano', 'harpsichord', 'fortepiano', 'organ', 'collaborative piano', 'jazz piano'):
                if 'Faculty Recital' in event_tags:
                    performer_type = 'Faculty'
                else:
                    performer_type = 'Student'
                csv_event_name = f'Juilliard {performer_type} Recital: {student}, {instrument} with Collaborative Piano'
            else:
                # Unusual -- possibly piano duo, collaborative, organ or harpsichord
                csv_event_name = f'Juilliard Student Recital: {student}, {instrument}'
        elif is_precollege and \
                is_relevant_to_site(event_name_from_page) and \
                'pre-college faculty' not in event_name_from_page.lower() and \
                program_list_element and \
                program_list_element.find_all('p'):
            # Pre-college recital
            performers = []
            performers_html = ['<b>Pre-College Performers</b>', '']
            first_time = None
            for performer in program_list_element.find_all('p'):
                performer_text = str(performer.contents[0])
                # Relevant performers in bold
                if is_relevant_to_site(performer_text):
                    def remove_tag_if_exists(tag):
                        if tag in event_tags:
                            event_tags.remove(tag)
                    remove_tag_if_exists('Ensemble')
                    remove_tag_if_exists('Collaborative')
                    event_tags.append('Pure Keyboard')
                    event_tags.append('Solo')

                    # Make the line containing the relevant performer bold
                    performers_html.append('<b>{0}</b>'.format(performer_text))

                    # Pull out the performer's name and instrument
                    # '4:30pm - James Galway, Flute'
                    match = re.search('^(.+) - (.+), *(.+)$', performer_text)
                    if match:
                        start_str, performer, instrument = match.groups()
                        # Occasional pages have the time with a space before the AM/PM
                        start_str = start_str.replace(' AM', 'AM')
                        start_str = start_str.replace(' PM', 'PM')
                        start_time = dt.datetime.strptime(start_str, '%I:%M%p')
                        if not first_time:
                            first_time = start_time
                        end_time = start_time + dt.timedelta(hours=1)

                        if performer_text.lower().endswith(', piano'):
                            # Exclude the instrument 'James Smith' (piano is implied)
                            performer_title = '{1}'.format(*match.groups())
                        else:
                            # Include the instrument 'James Smith, Harpsichord'
                            performer_title = '{1} ({2})'.format(*match.groups())
                        performers.append(performer_title)

                else:
                    performers_html.append(performer_text)

            # Special event time for pre-college
            if first_time:
                start_dt = dt.datetime.combine(event_dt.date(), first_time.time())
                end_dt   = dt.datetime.combine(event_dt.date(), end_time.time())
                set_start_end_fields_from_start_dt(csv_dict, start_dt, end_dt)
            # Special event description pre-college
            csv_dict['event_description'] = '\r\n'.join(performers_html)

            if not performers:
                csv_event_name = 'Juilliard Non-Keyboard Pre-College Recitals'
            elif len(performers) > 1:
                csv_event_name = 'Juilliard Pre-College Recitals: {0}'.format(','.join(performers))
            else:
                csv_event_name = 'Juilliard Pre-College Recital: {0}'.format(performers[0])

        elif venue == VENUE_TRANSLATIONS['']:
            # Event is at Juilliard
            csv_event_name = f'{event_name_from_page}, at {venue}'
        else:
            # Not at Juilliard and not solo and not pre-college
            if 'Juilliard' in event_name_from_page or 'Juilliard' in venue:
                csv_event_name = f'{event_name_from_page}, at {venue}'
            else:
                csv_event_name = f'Juilliard {event_name_from_page}, at {venue}'

        if is_precollege:
            csv_event_name = csv_event_name.replace('Student Recital', 'Pre-College Recital')

        if 'Faculty Recital' in event_tags:
            csv_event_name = csv_event_name.replace('Student Recital', 'Faculty Recital')
            if 'Student Recital' in event_tags:
                event_tags.remove('Student Recital')
            if 'Young Performer' in event_tags:
                event_tags.remove('Young Performer')

        if 'collaborative pian' in description_html.lower():
            event_tags.append('Collaborative')
            
        csv_dict['event_name'] = csv_event_name
        csv_dict['event_tags'] = ','.join(set(event_tags))
        csv_dict['relevant'] = relevant

        return csv_dict
