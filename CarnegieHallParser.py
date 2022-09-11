from datetime import datetime
from EventParser import EventParser
from parser_common_code import any_match, set_start_end_fields_from_start_dt, parse_event_tags, set_relevant_from_dict, \
    initialize_csv_dict

CARNEGIE_DEFAULT_IMAGE_URL = 'https://carnegiehall.imgix.net/-/media/CarnegieHall/Images/About/Building-Overview/Carnegie-Hall-facade.jpg'
CARNEGIE_DEFAULT_IMAGE_URL = 'https://carnegiehall.imgix.net/-/media/CarnegieHall/Images/About/Rentals/Carnegie-Hall-Exterior-at-Night.jpg'


class CarnegieHallParser(EventParser):

    def parse_soup_to_event(self, url, soup):
        """Parses a soup object into a dictionary whose keys are the CSV rows
        required by the imported CSV
        """

        venue_translations = {
            'Arthur Zankel Music Center, Helen Filene Ladd Concert Hall': 'Carnegie Hall',
            'BRIC House':                         'BRIC House',
            'Brooklyn Museum':                    'Brooklyn Museum',
            'Brooklyn Public Library, Central Library': 'Brooklyn Central Public Library',
            'Danspace Project':                   'St. Mark’s Church-In-The-Bowery',
            'El Museo del Barrio':                'El Museo del Barrio',
            'Flushing Town Hall':                 'Flushing Town Hall',
            'Goethe-Institut':                    None,
            'Harlem Stage Gatehouse':             'Harlem Stage Gatehouse',
            'Italian Academy for Advanced Studies in America at Columbia University':
                'Italian Academy for Advanced Studies, Columbia University',
            'Jackson Heights Branch Library (QL)':'Queens Library at Jackson Heights',
            'Ladd Concert Hall':                  None,
            'LaGuardia Performing Arts Center':   'LaGuardia Performing Arts Center',
            'Marlene Meyerson JCC Manhattan': 'Marlene Meyerson JCC Manhattan',
            'Morgan Library & Museum':            'The Morgan Library and Museum',
            'New York Hall of Science':           'New York Hall of Science',
            'New York Public Library for the Performing Arts': 'New York Public Library for the Performing Arts',
            'Our Saviour\'s Atonement Lutheran Church': 'Our Saviour\'s Atonement Lutheran Church',
            'Paul Hall':                          'Juilliard School',
            'Philharmonie de Paris':              None,
            'Pregones Theater':                   'Pregones Theater',
            'Resnick Education Wing':             'Carnegie Hall',
            'Schomburg Center for Research in Black Culture': 'Schomburg Center for Research in Black Culture',
            'St. Michael\'s Church':              'St. Michael\'s Church',
            'Stern Auditorium / Perelman Stage':  'Carnegie Hall',
            'Weill Recital Hall':                 'Carnegie Hall',
            'YIVO Institute for Jewish Research': 'YIVO Institute for Jewish Research',
            'Zankel Hall':                        'Carnegie Hall',
            'Zankel Hall Center Stage':           'Carnegie Hall',
        }

        csv_dict = initialize_csv_dict(url)

        # We will raise an error below if the venue is unknown, but only if the event is relevant
        try:
            venue_from_page = soup.find('span', attrs={'class': 'location', 'itemprop': 'name'}).contents[0].strip()
        except AttributeError as ex:
            print('Unable to find venue in event page')
            return None
        venue = csv_dict["venue_name"] = venue_translations.get(venue_from_page, venue_from_page)
        if not venue:
            # Venue intentionally specified to skip, e.g., if out of town
            print(f'Skipping event at venue {venue_from_page}')
            return None
        csv_dict["venue_name"] = venue

        # Date/time example: 'Sunday, October 23, 2016 | 2 PM'
        event_date = soup.find("div", attrs={"class":"ch-page-title__details"}).find("span", attrs={"class":"date"}).contents[0].strip()
        event_time = soup.find("div", attrs={"class":"ch-page-title__details"}).find("span", attrs={"class":"time"}).contents[0].strip()
        event_dt = "{0} {1}".format(event_date, event_time)

        try:
            # Sunday, April 29, 2018 2 PM
            dt = datetime.strptime(event_dt.strip(), "%A, %B  %d, %Y %I %p")
        except Exception as ex:
            # Sunday, April 29, 2018 2:30 PM
            dt = datetime.strptime(event_dt.strip(), "%A, %B  %d, %Y %I:%M %p")
        #print("Parsed '{0}' to {1}".format(event_dt.strip(), dt))

        set_start_end_fields_from_start_dt(csv_dict, dt)

        try:
            # https://carnegiehall.imgix.net/-/media/CarnegieHall/Images/Events/2018-2019-CH-Presents/Denis-Matsuev.jpg?w=690&h=690&fit=crop&crop=faces
            image_url = soup.find("meta", attrs={"property":"og:image:url"})["content"].split("?")[0]
        except Exception as ex:
            image_url = CARNEGIE_DEFAULT_IMAGE_URL
            #print("No image URL found in {0}".format(url))
        csv_dict["external_image_url"] = image_url

        # Performers
        performers = soup.find("div", attrs={"class":"ch-event-performers"})
        if performers:
            performer_items = performers.p or performers.span
            try:
                performers = []
                for p in performer_items.contents:
                    p = str(p).replace('<br>', '').replace('<br/>', '').strip()
                    if p:
                        # Keyboardists in bold
                        if False and any_match(('piano', 'pianist', 'organ', 'harpsichord'), p):
                            p = f'<b>{p}</b>'

                        performers.append(p)

            except Exception as ex:
                raise

        if performers:
            heading = 'Performer' if len(performers) == 1 else 'Performers'
            performer_rows = [f'<strong>{heading}</strong>'] + performers
        else:
            performer_rows = ['']

        # Program
        program_works = None
        program_work_div = soup.find("div", attrs={"class": "ch-event-repertoires"})
        if program_work_div:
            program_works = ''.join([str(d) for d in program_work_div.find_all('div')])
            program_works = ''.join([l for l in program_works.split('\n') if '<div' not in l])
            program_works = program_works.replace('<p>', '<br/>').replace('</p>', '')
            program_section = '<strong>Program</strong>' + program_works
        else:
            program_section = ''

        # Description
        description_element = soup.find('div', attrs={'class': 'bigger', 'itemprop': 'description'})
        if description_element:
            description_rows = [str(c) for c in description_element.contents]
        else:
            description_rows = []
        description_html = '<br />'.join(performer_rows) + '<br /><br />' + ''.join(description_rows)

        body_html = description_html + '<br /><br />' + '<br />' + program_section
        csv_dict["event_description"] = body_html

        # Event name
        event_name_element = soup.find("h1", attrs={"class":"ch-page-title__title"})
        if event_name_element:
            # ['Evgeny Kissin, Piano', 'Emerson String Quartet']
            event_name_lines = [str(line).strip() for line in event_name_element.contents
                                if str(line).strip() and not str(line).strip().startswith('<')]
            event_name = "; ".join(event_name_lines)
            if performers and (len(performers) == 1) and event_name.endswith(", Piano"):
                # If a soloist, 'piano' is redundant
                event_name = f'{performers[0]} Solo Recital'
            elif performers:
                # Add the pianist's name if not the headliner
                for performer in performers:
                    # Don't add the performer to the event description if they are already there
                    if performer in event_name:
                        continue
                    if "piano" in performer.lower():
                        event_name += "; {0},".format(performer.replace('�', '').strip())
                        break;
            event_name = f'{event_name} at {venue}'
            event_name = event_name.replace(', Piano Solo Recital', ' Solo Recital')
            csv_dict["event_name"] = event_name
        else:
            event_name = ''

        # Event tags
        event_tags = ["Classical"]
        if performers:
            if len(performers) == 1:
                event_tags.append("Solo")
                event_tags.append("Pure Keyboard")
            else:
                event_tags.append("Ensemble")

        event_text = '<br />'.join((csv_dict['event_name'], csv_dict['event_description']))
        parse_event_tags(csv_dict, event_tags, event_text)
        csv_dict["event_tags"] = ",".join(event_tags)

        # Relevant
        relevant = set_relevant_from_dict(csv_dict, include_accompanied=False)
        if relevant and not venue_from_page in venue_translations:
            raise RuntimeError(f'Unknown venue: {venue_from_page}')

        # Price is retrieved dynamically and is not available in the page source
        soup.find_all('div', attrs={'class': 'buybutton'})

        return csv_dict
