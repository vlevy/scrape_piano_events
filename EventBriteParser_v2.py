import json
import os
from datetime import datetime
from pathlib import PurePath
from time import sleep

import importer_globals as G
from EventParser import EventParser
from parser_common_code import (
    encode_html,
    initialize_csv_dict,
    is_in_new_york,
    parse_price_range,
    parse_url_to_soup,
    set_relevant_from_dict,
    set_start_end_fields_from_start_dt,
    set_tags_from_dict,
    sleep_random,
)


class EventBriteParser_v2(EventParser):
    VENUES = {
        '468 W 143rd St': 'Our Lady of Lourdes School',
        'Alianza Dominicana Cultural Center': None,
        'ALPHAVILLE': None,
        'Artists Space': None,
        'Bar Freda': None,
        'Baruch Performing Arts Center': None,
        'Birdland Jazz Club': 'Birdland',
        'Birdland Theater': 'Birdland',
        'Bloomingdale School of Music': None,
        'Blue Gallery': None,
        'Bohemian National Hall': None,
        'Brooklyn Conservatory of Music': None,
        'Bruno Walter Auditorium': None,
        'Cafe Wha?': None,
        'Christ &amp; St Stephen&#39;s Church': 'Christ & St. Stephen\'s Episcopal Church',
        'Church In the Gardens': None,
        'Church of the Holy Apostles': None,
        'Church Of The Redeemer Astoria': 'The Church of the Redeemer in Astoria',
        'CitySpire': None,
        'CRS (Center for Remembering &amp; Sharing)': 'CRS (Center for Remembering & Sharing)',
        'Cultural Center, Lycée Français de New York': 'Lycée Français de New York',
        'DiMenna Center for Classical Music': None,
        'Dream House': None,
        'Fiction Bar/Cafe': None,
        'Fiorello H. LaGuardia High School of Music & Art and Performing Arts Concert Hall': 'Fiorello H. LaGuardia High School of Music & Art and Performing Arts',
        'First Unitarian Church of Brooklyn': None,
        'First Unitarian Congregational Society in Brooklyn': None,
        'French Consulate in New York,': 'Consulate General of France',
        'Good Judy': 'skip',
        'Good Shepherd-Faith Presbyterian Church': None,
        'Groove': None,
        'Hoff-Barthelson Music School': 'skip',
        'House of the Redeemer': None,
        'Hungarian House': None,
        'Hunter Hall': 'skip',
        'Jamaica Center for Arts and Learning (JCAL)': 'Jamaica Center for Arts and Learning',
        'Katra Lounge & Event Space': None,
        'Katra Lounge &amp; Event Space': 'Katra Lounge & Event Space',
        'Kaufman Music Center': 'Merkin Concert Hall at Kaufman Music Center',
        'Klavierhaus': None,
        'Klavierhaus NYC': 'Klavierhaus',
        'Kostabi World Chelsea': None,
        'Lamington Presbyterian Church': 'skip',
        'Leonia United Methodist Church': None,
        'Louis Armstrong House Museum': None,
        'Mark Morris Dance Group': None,
        'Merkin Hall': 'Merkin Concert Hall at Kaufman Music Center',
        'Michiko Rehearsal Studios': None,
        'Minton’s Playhouse': None,
        'Morris Knolls High School': 'skip',
        'Morristown': 'skip',
        'Most Holy Redeemer Roman Catholic Church': None,
        'National Opera Center': 'Opera America',
        'New York Public Library for the Performing Arts -Bruno Walter Auditorium': 'Bruno Walter Auditorium',
        'Old Stone House of Brooklyn': None,
        'ONX Studio': None,
        'OPERA America&#39;s National Opera Center Rehearsal Hall': 'Opera America',
        'OPERA America&#39;s National Opera Center': 'Opera America',
        'OPERA America': 'Opera America',
        'OPERA America\'s National Opera Center Rehearsal Hall' : 'Opera America',
        'OPERA America\'s National Opera Center': 'Opera America',
        'OPERA America’s National Opera Center Rehearsal Hall': 'Opera America',
        'OPERA America’s National Opera Center': 'Opera America',
        'Parkside Lounge': None,
        'Pequot Library': 'skip',
        'Piano Works In Progress': 'Piano Works in Progress',
        'Pianos': 'skip',
        'Pianos, Ludlow Street, New York, NY, USA': 'skip',
        'Pino&#39;s Gift Basket Shoppe and Wine Cellar': 'skip',
        'Pioneer Works': None,
        'PNC Bank Arts Center': 'skip',
        'Quantum Brooklyn': None,
        'Rainbow Room': None,
        'Redeemer Episcopal Church': 'The Church of the Redeemer in Astoria',
        'Roulette Intermedium': None,
        'Saint John&#39;s In the Village': 'St. John\'s in the Village Episcopal Church',
        'Saint John’s In the Village': 'St. John\'s in the Village Episcopal Church',
        'Saint Peter&#39;s Church': 'Saint Peter\'s Church',
        'Scholes Street Studio': None,
        'Soapbox Gallery': None,
        'South Presbyterian Church': None,
        'St Paul&#39;s United Methodist Church': 'St Paul\'s United Methodist Church',
        'St Paul’s United Methodist Church': 'St Paul\'s United Methodist Church',
        'St. John\'s in the Village Episcopal Church': None,
        'St John\'s in the village, St Benedict\'s Courtyard': 'St. John\'s in the Village Episcopal Church',
        'St. John\'s in the Village': 'St. John\'s in the Village Episcopal Church',
        'St. John’s in the Village Episcopal Church': 'St. John\'s in the Village Episcopal Church',
        'Tenri Cultural Institute': None,
        'Tenri Cultural Institute of New York': 'Tenri Cultural Institute',
        'TENRI Cultural Institute of New York': 'Tenri Cultural Institute',
        'The Brick Presbyterian Church': None,
        'The Brooklyn Monarch': None,
        'The Church of the Transfiguration': None,
        'The College of New Jersey': 'skip',
        'The Cutting Room': None,
        'The DiMenna Center for Classical Music': 'DiMenna Center for Classical Music',
        'The Flamboyan Theater at The Clemente': 'The Clemente Soto Vélez Cultural & Educational Center',
        'The Great Hall': 'The Great Hall at Cooper Union',
        'The National Arts Club': None,
        'The National Jazz Museum in Harlem': 'National Jazz Museum in Harlem',
        'The Presbyterian Church of Chatham Township': 'skip',
        'The Stonewall Inn': None,
        'Theater at St. Jean': None,
        'Third Street Music School Settlement': None,
        'Threes Brewing': 'Threes Brewing Greenpoint Bar & Beer Shop',
        'Topaz Arts Inc': None,
        'Ukrainian Institute of America': None,
        'Union Arts Center': 'skip',
        'W83 Auditorium': 'W83 Ministry Center',
        'West Side Presbyterian Church': 'West Side Presbyterian Church in Ridgewood',
        'Willow Hall': 'skip',
    }


    EXISTING_VENUES = (
        '1200 Broadway',
        '1277 Flushing Ave',
        '218 West 11th Street',
        '221 N 9th St',
        '244 Rehearsal Studios',
        '244 Waverly Place',
        '28 Liberty St',
        '67th Street Library',
        '92nd Street Y',
        '96th Street Library',
        'A Soho Loft',
        'Aaron Copland School of Music',
        'Aaron Davis Hall, City College',
        'Abyssinian Baptist Church',
        'AC Pianocraft',
        'Acoustik Garden Lounge',
        'Adelphi University Performing Arts Center',
        'Advent Lutheran Church',
        'Ailey Citigroup Theater',
        'Alianza Dominicana Cultural Center',
        'Alice Tully Hall at Lincoln Center',
        'All Saints Church',
        'All Souls Church',
        'ALPHAVILLE',
        'Alvin Johnson/J.M. Kaplan Hall',
        'Amaya',
        'American Irish Historical Society',
        'Americas Society',
        'Andrew Heiskell Braille and Talking Book Library',
        'Anna Maria Kellen Concert Hall',
        'Anna-Maria and Stephen Kellen Auditorium',
        'Anna-Maria and Stephen Kellen Gallery at Parsons School of Design',
        'Anne Goodman Recital Hall, Kaufman Center',
        'Anthology Film Archives',
        'Aret� Venue and Gallery',
        'Arlo NoMad',
        'Arnhold Hall at the New School',
        'Artists Space',
        'Austrian Cultural Forum',
        'Avram Theater',
        'BAM Fisher',
        'BAM Howard Gilman Opera House',
        'Bar Freda',
        'Bar Nine',
        'Bargemusic',
        'Baruch Performing Arts Center',
        'Battery Park',
        'Baza Studio NYC',
        'Beacon Theatre',
        'Bern Dibner Library, Pfizer Auditorium',
        'Bethany Baptist Church, Newark',
        'Birdland',
        'Black Box Performing Arts Center',
        'Bloomingdale School of Music',
        'Blue Gallery',
        'Blue Note',
        'Bohemian National Hall',
        'BRIC',
        'BRIC House',
        'Bridgehampton Presbyterian Church',
        'Broadway Comedy Club',
        'Broadway Presbyterian Church',
        'Bronx Library Center, Auditorium',
        'Bronx River Art Center',
        'Bronxville Womens Club',
        'Brookhaven National Laboratory',
        'Brooklyn Bridge Park, Pier 1',
        'Brooklyn Center for the Arts',
        'Brooklyn Central Public Library',
        'Brooklyn Comedy Collective',
        'Brooklyn Conservatory of Music',
        'Brooklyn Museum',
        'Brooklyn Music School',
        'Brooklyn Opera House',
        'Bruno Walter Auditorium',
        'Bryant Park, Upper Terrace',
        'Buttenwieser Hall at 92nd St Y',
        'Cafe Bohemia',
        'Cafe Wha?',
        'Caffe Vivaldi',
        'Caramoor Center for Music and the Arts',
        'Carnegie East House',
        'Carnegie Hall',
        'Casa Italiana Zerilli - Marimo at NYU',
        'Caspary Auditorium at The Rockefeller University',
        'Cathedral of St. John the Divine',
        'Center for Jewish History',
        'Central Park at Grant Hill',
        'Central Park Great Hill',
        'Central Presbyterian Church',
        'Central Synagogue',
        'Chatham Square Library',
        'Chatty Pianist Salon',
        'Chelsea Factory',
        'Christ & St. Stephen\'s Episcopal Church',
        'Christ Church NYC',
        'Christ Church Riverdale',
        'Church In the Gardens',
        'Church of St. Edward the Martyr',
        'Church of St. Ignatius Loyola',
        'Church of St. Joseph of the Holy Family',
        'Church of the Blessed Sacrament',
        'Church of the Epiphany',
        'Church of the Heavenly Rest',
        'Church of the Holy Apostles',
        'Church St School For Music and Art',
        'Cinema Arts Center, Huntington',
        'City Spire Condominium',
        'City Vineyard',
        'CitySpire',
        'Claire Tow Theater',
        'Claret Wine Bar',
        'Clark Studio Theater',
        'Clove Lakes Park',
        'Club Bonafide',
        'Club Cumming',
        'Co-Cathedral of St. Joseph',
        'Cobble Hill Cinemas',
        'Coe Hall at Planting Fields Arboretum',
        'Cold Spring Harbor Laboratory',
        'College of Mt. St. Vincent',
        'Columbia Maison Fran�aise',
        'Columbia University',
        'Columbus Library',
        'Community Church of Little Neck',
        'Community Church of New York',
        'Concert Hall',
        'Consulate General of Argentina',
        'Consulate General of France',
        'Consulate General of Hungary',
        'Consulate General of Poland',
        'Consulate General of the Republic of Bulgaria',
        'Corpus Christi Church',
        'Crotona Park',
        'CRS (Center for Remembering & Sharing)',
        'Crypt Chapel of The Church of the Intercession',
        'Cupping Room Cafe',
        'Czech Center New York',
        'Daniel and Joanna S. Rose Studio at Lincoln Center',
        'David Geffen Hall at Lincoln Center',
        'David H. Koch Theater',
        'David Rubenstein Atrium at Lincoln Center',
        'Deutsches Haus at NYU',
        'Diller-Quaile School of Music',
        'DiMenna Center for Classical Music',
        'Dizzy\'s Club Coca Cola',
        'Donald and Mary Oenslager Gallery at Lincoln Center',
        'Dorot',
        'Dream House',
        'Drom',
        'Earl Hall at Columbia University',
        'Edenwald Library',
        'El Museo del Barrio',
        'Elebash Recital Hall, The Graduate Center',
        'Elim International Fellowship',
        'Elmont Library',
        'Engelman Recital Hall, Baruch College',
        'Englewood Public Library',
        'Estonian House',
        'Eugene Lang College of Liberal Arts at The New School',
        'Evans Real Estate Investments',
        'Faculty House at Columbia University',
        'Faust Harrison Pianos',
        'FIAF, Florence Gould Hall',
        'Film Forum',
        'First AME Church: Bethel',
        'First Unitarian Church of Brooklyn',
        'First Unitarian Congregational Society in Brooklyn',
        'Flushing Town Hall',
        'Flying Solo',
        'Fort Lee Public Library',
        'Francesca Beale Theater',
        'Frank T. Modica Community Room',
        'Frank T. Modica Room',
        'French Consulate',
        'Full Gospel Assembly',
        'Future Space',
        'Gallery MC',
        'Gallery Shchukin',
        'General Society of Mechanics & Tradesmen',
        'Gerald W. Lynch Theater at John Jay College',
        'German Lutheran Church of St. Paul',
        'Glass Box Performance Space at the New School',
        'Goddard Riverside\'s Bernie Wohl Center',
        'Good Judy',
        'Good Shepherd Faith Presbyterian  Church',
        'Good Shepherd-Faith Presbyterian Church',
        'Grace and St. Paul\'s Church',
        'Grace Lutheran Church',
        'Graduate Center CUNYH',
        'Greater Calvary Baptist Church',
        'Green-Wood Cemetery',
        'Greenwich House Music School',
        'Greenwich Library',
        'Greylock Records',
        'Grinberg Classical Salon',
        'Groove',
        'Harlem Stage Gatehouse',
        'Hearst Plaza at Lincoln Center',
        'Helen Mills Event Space and Theater',
        'Hell\'s Kitchen Area',
        'High Bar',
        'Holy Trinity Lutheran Church',
        'House of the Redeemer',
        'Hudson Eats',
        'Hunter College (Hall TBA)',
        'Industry City Bandshell in Courtyard 1/2',
        'Ingalls Recital Hall (Rossey Hall, Room 101), New Jersey City University',
        'Interface NYC',
        'Inwood Art Works Culture Hub',
        'Italian Academy for Advanced Studies, Columbia University',
        'Jackie Robinson Park',
        'Jackie Robinson Recreation Center',
        'Jamaica Center for Arts and Learning',
        'Jamaica Performing Arts Center',
        'Joe\'s Pub',
        'John J. Cali School Of Music, Montclair State University',
        'John L. Tishman Auditorium, University Center',
        'Judson Memorial Church',
        'Juilliard School',
        'Julius\'s Bar',
        'Katra Lounge & Event Space',
        'Kaye Playhouse at Hunter College',
        'Keiko Studios Music Academy',
        'Kittay House',
        'Klavierhaus',
        'Kostabi World Chelsea',
        'Kostabi World Uptown',
        'Kumble Theater',
        'Kupferberg Center for the Arts',
        'La Nacional',
        'Lafayette Avenue Presbyterian Church',
        'LaGuardia Performing Arts Center',
        'Lang Recital Hall at Hunter College',
        'Le Poisson Rouge',
        'LeFrak Concert Hall',
        'Legendary Republic',
        'Lehman College Art Gallery',
        'Lenox Hill Neighborhood House',
        'Leonard & Claire Tow Center for the Performing Arts',
        'Leonia Public Library',
        'Liederkranz Foundation',
        'Lincoln Center',
        'Lincoln Center Plaza',
        'Lincoln Center\'s Rose Theater at Time Warner Center',
        'Lincoln Centre',
        'Lincoln Square',
        'Liszt Institute',
        'Locust Valley Library',
        'Loove Labs',
        'Louis Armstrong House Museum',
        'Louis K. Meisel Gallery',
        'Lyc�e Fran�ais de New York',
        'Macomb\'s Bridge Library',
        'Madison Avenue Presbyterian Church',
        'Mana Contemporary',
        'Manhattan School of Music',
        'Marble Collegiate Church',
        'Mark Morris Dance Group',
        'Marlene Meyerson JCC Manhattan',
        'Members Only',
        'Merkin Concert Hall at Kaufman Music Center',
        'Metropolis Ensemble',
        'Metropolitan Museum of Art',
        'Metropolitan Opera House',
        'Mezzrow',
        'Michiko Rehearsal Studios',
        'Michiko Studios',
        'Miller Theatre at Columbia University',
        'Milton Resnick and Pat Passlof Foundation',
        'Minton\'s Playhouse',
        'MISE-EN_PLACE Bushwick',
        'MISE-EN_PLACE Greenpoint',
        'MIST Harlem',
        'Mitzi E. Newhouse Theater',
        'Montclair Brewery',
        'Morris Park Library',
        'Most Holy Redeemer Roman Catholic Church',
        'Mount Morris Ascension Presbyterian Church',
        'Museum of Jewish Heritage',
        'National Arts Club',
        'National Jazz Museum in Harlem',
        'National Sawdust',
        'Neidorff-Karpati Hall',
        'Neue Galerie',
        'New Jersey Performing Arts Center',
        'New York Hall of Science',
        'New York Jazz Workshop',
        'New York Manhattan Church of the Advent Hope Seventh-Day Adventist Church',
        'New York Presbyterian Church',
        'New York Public Library for the Performing Arts',
        'New York Society for Ethical Culture',
        'New York Studio School of Drawing, Painting and Sculpture',
        'Newark Symphony Hall',
        'Nicholas Roerich Museum',
        'Noel Pointer Foundation',
        'Nook',
        'NYU C205',
        'NYU Frederick Loewe Theatre',
        'Old Stone House of Brooklyn',
        'Old Westbury Gardens',
        'Online Venue',
        'Opera America',
        'Ottendorfer Library',
        'Our Lady of Lourdes School',
        'Our Saviour\'s Atonement Lutheran Church',
        'Paley Center for Media',
        'Pangea',
        'Paracademia Center Inc',
        'Park Avenue Armory',
        'Park Church Co-op',
        'Pelham Bay Library',
        'Pete\'s Candy Store',
        'Piano on Park',
        'Piano Works in Progress',
        'PianoPiano Rehearsal Studios',
        'Pioneer Works',
        'Port Washington Library',
        'Pregones Theater',
        'PS 321',
        'Queens Library (Central)',
        'Queens Library at Jackson Heights',
        'Rainbow Room',
        'Rattle & Hum West',
        'Resnick Education Wing at Carnegie Hall',
        'Revelation Gallery',
        'Richmondtown Library, Staten Island',
        'Ripley-Grier Studios',
        'Riverside Church',
        'Rockwood Music Hall',
        'Romanian Cultural Center',
        'Romanian Cultural Institute of New York',
        'Room 603',
        'Rosemary and Meredith Willson Theater',
        'Rosemary and Meredith Willson Theater at Juilliard School',
        'Roulette',
        'Roulette Intermedium',
        'Rubin Museum',
        'Rumsey Playfield',
        'Rutgers Presbyterian Church Sanctuary',
        'Saint John\'s Episcopal Church',
        'Saint Peter\'s Chelsea',
        'Saint Peter\'s Church',
        'Saint Thomas Church Fifth Avenue',
        'Salmagundi Club',
        'Samuel B. & David Rose Building',
        'San Damiano Mission Catholic Church',
        'Scandinavia House',
        'Scholes Street Studio',
        'Schomburg Center for Research in Black Culture',
        'Seward Park',
        'Shapeshifter Lab',
        'Sheen Center for Thought and Culture',
        'Shetler Studios',
        'Sid Gold\'s Request Room',
        'Singers',
        'Sisters',
        'Smalls Live',
        'Smoke Jazz',
        'Soapbox Gallery',
        'SOB\'s',
        'Soccer Roof',
        'Society of Jewish Science',
        'Socrates Sculpture Park',
        'Sony Hall',
        'Sound Of Brazil',
        'Soundworks Recording Studio',
        'South Oxford Space',
        'Southampton Cultural Center',
        'Southamton Arts Center',
        'Spectrum',
        'St Jean Baptiste Church',
        'St John\'s in the Village',
        'St John\'s Lutheran Church',
        'St Mark\'s Episcopal Church',
        'St Paul\'s United Methodist Church',
        'St Stephen\'s Church',
        'St. Ann & the Holy Trinity Church',
        'St. Barts Park Avenue',
        'St. Jean Baptiste Church',
        'St. John\'s in the Village Episcopal Church',
        'St. Luke\'s Episcopal Church',
        'St. Mark\'s Church-In-The-Bowery',
        'St. Michael\'s Church',
        'St. Paul & St. Andrew United Methodist Church',
        'St. Peter\'s Chelsea',
        'Stanley H. Kaplan Penthouse at Lincoln Center',
        'Steinway Hall',
        'Steinway Piano Gallery Paramus',
        'Stephanie P. McClelland Drama Theater',
        'Stephen Wise Free Synagogue',
        'Stern Auditorium / Perelman Stage at Carnegie Hall',
        'SubCulture',
        'Subrosa',
        'Swing 46',
        'Symphony Space',
        'Tenri Cultural Institute',
        'The Appel Room at Lincoln Center',
        'The Brick Presbyterian Church',
        'The Cell Theatre',
        'The Church of Saint Mary the Virgin',
        'The Church of the Redeemer in Astoria',
        'The Church of the Transfiguration',
        'The Clemente Soto V�lez Cultural & Educational Center',
        'The Cornelia Street Caf�',
        'The Cutting Room',
        'The Delancey',
        'The Drawing Room',
        'The Duplex Cabaret Theatre',
        'The Explorers Club',
        'The Flea Theater',
        'The Frick Collection',
        'The German House',
        'The Great Hall at Cooper Union',
        'The Green Room 42',
        'The Greene Space',
        'The Interchurch Center',
        'The Jazz Gallery',
        'The Kitano',
        'The Kitchen',
        'The Knockdown Center',
        'The Kosciuszko Foundation',
        'The Local NY',
        'The Madison Theatre at Molloy College',
        'The Morgan Library and Museum',
        'The National Arts Club',
        'The New School',
        'The New School University Center',
        'The New School, Albert and Vera List Academic Center',
        'The Poetry Project',
        'The Stonewall Inn',
        'The Town Hall',
        'The Union Club',
        'The William Vale',
        'Theatre Works USA',
        'Third Street Music School Settlement',
        'Threes Brewing Greenpoint Bar & Beer Shop',
        'Tilles Center for the Performing Arts',
        'Time Warner Center',
        'Times Center',
        'Tompkins Square Library',
        'Topaz Arts Inc',
        'Tremont Library',
        'Tribeca Synagogue',
        'Trinity School',
        'Tudor City Steakhouse',
        'Turtle Bay Music School',
        'Ukrainian Institute of America',
        'Ukrainian Museum',
        'Uncommonly Studio',
        'Union Hall',
        'Union Square',
        'Union Temple at Grand Army Plaza',
        'Unitarian Universalist Congregation of Central Nassau',
        'United Nations',
        'Untermyer Gardens Conservancy',
        'Videology Bar & Cinema',
        'Village Vanguard',
        'Virginia Park',
        'Vivian Beaumont Theater',
        'W83 Auditorium',
        'Walter Reade Theater at Lincoln Center',
        'Washington Irving High School',
        'Weill Recital Hall, Carnegie Hall',
        'West Side Presbyterian Church in Ridgewood',
        'West St Brooklyn',
        'Williams Residence',
        'Williamsburg Opera House',
        'Yamaha Artists Piano Salon',
        'YIVO Institute for Jewish Research',
        'Zankel Hall, Carnegie Hall',
        'Zinc Bar',
        'Zoom',
    )


    @staticmethod
    def filter_event(soup):
        # If we got an expired event, don't use it
        ended = soup.find('class', attrs={'span', 'expired-badge'})
        if ended:
            return None
        else:
            return soup


    @staticmethod
    def read_urls(url_file_name):
        """Read the event-page URLs for the first 10 pages of piano events in Manhattan
        """
        urls = set()
        for page in range(10):
            sleep_random()
            url_this_page = f'https://www.eventbrite.com/d/ny--new-york/piano/?mode=search&page={page+1}'
            print('Reading URL {0}'.format(url_this_page))

            soup = parse_url_to_soup(url_this_page)

            links = soup.find_all('a', attrs={'class': 'event-card-link'})
            for link in links:
                url_this_event = link['href'].split('?')[0]
                urls.add(url_this_event)

        # Write the URLs out to a file for safekeeping
        url_file_path = PurePath('../Data', url_file_name)
        with open(url_file_path, 'w', newline='\n') as url_file:
            for url_this_page in urls:
                url_file.write(url_this_page + '\n')

        return list(urls)

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

        # Don't accept any events without a location
        try:
            latitude = float(soup.find("meta", attrs={'property': 'event:location:latitude'})['content'])
            longitude = float(soup.find("meta", attrs={'property': 'event:location:longitude'})['content'])
        except Exception as ex:
            print('Listing location was not specified')
            return None
        
        # Don't accept any events outside of New York
        if not is_in_new_york(latitude, longitude):
            print('Venue is outside of New York')
            return None

        tags_list = ['EB']
        # "2018-03-25T17:00:00-04:00"
        try:
            date_string = event_details['startDate'][:19]
            start_dt = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S')
            if not start_dt:
                raise RuntimeError(f'Unable to find start date from {start_dt}')
            end_dt   = datetime.strptime(event_details['endDate'][:19], '%Y-%m-%dT%H:%M:%S')
            if not end_dt:
                raise RuntimeError(f'Unable to find end date from {start_dt}')
            set_start_end_fields_from_start_dt(csv_dict, start_dt, end_dt)
        except KeyError as ex:
            print(f'Unable to parse start and/or end date: {ex}')
            return None

        try:
            csv_dict['event_name'] = '{0} at {1}'.format(event_details['name'], event_details['location']['name'])
        except KeyError as ex:
            print('Event name not found. Skipping.')
            return None

        venue_from_page = str(event_details['location']['name']).strip()
        venue = EventBriteParser_v2.VENUES.get(venue_from_page, venue_from_page) or venue_from_page
        if venue == 'skip':
            print(f'Skipping event at unwanted venue "{venue_from_page}"')
            return None

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
        if 'at blue note' in csv_dict['event_name'].lower():
            return None
        if 'at mezzrow' in csv_dict['event_name'].lower():
            return None
        if 'at birdland jazz' in csv_dict['event_name'].lower():
            return None
        if 'upstairs lounge' in csv_dict['event_name'].lower():
            return None
        if 'dueling pianos' in csv_dict['event_name'].lower():
            return None
        if 'pianos showroom' in csv_dict['event_name'].lower():
            return None

        relevant = set_relevant_from_dict(csv_dict, include_accompanied=False)
        if not relevant:
            return None

        if venue not in EventBriteParser_v2.EXISTING_VENUES:
            print(f'Need to create venue {repr(venue)}')

        return csv_dict
