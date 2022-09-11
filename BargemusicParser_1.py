import re
from datetime import date, datetime
from EventParser import EventParser
from parser_common_code import remove_all

class BargemusicParser_1(EventParser):
    pass

    def parse_full_event_page(self, soup):
        """Parses a soup object containing the whole Bargemusic events page,
        into a dictionary whose keys are the CSV rows required by the imported CSV.
        The events page listing must have been edited to group separate dates into divs.
        """
        csv_rows = []


        # Loop over all of the months
        all_months = soup.find_all('div', attrs={'class': 'calendarmonth'})
        for month in all_months:

            # Pull out all of the event dates
            event_elements_in_month = month.find_all('div', attrs={'class': 'pianyc-event'})
            year_month_text = month.find('h2', attrs={'class': 'month'}).contents[1].strip() # 'March 2018'
            try:
                first_of_month = datetime.strptime(year_month_text, '%B %Y')
            except Exception as ex:
                raise

            for event_element in event_elements_in_month:
                event_tags = ['Classical']
                # -----------------------------------
                # Easy fields
                # -----------------------------------
                csv_dict = { \
                    'categories': LIVE_PERFORMANCE,
                    'show_map': 'TRUE',
                    'show_map_link': 'FALSE',
                    'venue_name': 'Bargemusic',
                }

                # Event name
                event_lines = [''.join([str(c) for c in line.contents]) for line in event_element.find_all('p', attrs={'class': ('calendarlisting', 'calendarlisting2')})]
                main_artists = [remove_all(str(artist.contents[0]), ('<strong>', '</strong>', ':')).strip()  for artist in event_element.find_all('p', attrs={'class': 'calendarartist'})]
                sub_artists  = [remove_all(str(artist.contents[0]), ('<strong>', '</strong>')).strip()       for artist in event_element.find_all('p', attrs={'class': 'calendarartist2'})]
                piano_artists = [remove_all(str(artist), ('<strong>', '</strong>')).strip()                  for artist in (main_artists + sub_artists) if is_pianyc_related(artist)]
                if piano_artists == main_artists:
                    # Solo piano: 'Christopher Beck at Bargemusic'
                    event_title = '{0} Solo Recital at Bargemusic'.format(' and '.join([a.replace(', piano', '') for a in piano_artists]))
                    event_tags.append('Solo')
                    event_tags.append('Pure Keyboard')
                elif sub_artists and ((main_artists + sub_artists) == piano_artists):
                    # Piano headliner with piano sub-artist 'Steven Beck with Yalin Chi at Bargemusic'
                    event_title = '{0} with {1} at Bargemusic'.format(' and '.join([a.replace(', piano', '') for a in main_artists]),
                                                                      ' and '.join([a.replace(', piano', '') for a in sub_artists]))
                    event_tags.append('Ensemble')
                    event_tags.append('Pure Keyboard')
                elif piano_artists and (piano_artists != main_artists):
                    # Piano artists are not the main artists: 'Cassatt String Quartet at Bargemusic; Doris Stevenson, Piano'
                    event_title = '{0} at Bargemusic; {1}'.format(' and '.join(main_artists), ' and '.join([a.replace(', piano', ', Piano') for a in piano_artists]))
                    event_tags.append('Ensemble')
                elif main_artists:
                    # Probably not a relevant event: 'Vera Vaidman, Violin at Bargemusic'
                    event_title = '{0} at Bargemusic'.format(' and '.join(main_artists))
                    event_tags.append('Ensemble')
                else:
                    raise ValueError('No event title category')
                csv_dict['event_name'] = event_title

                # Date and time
                date_element = event_element.find('p', attrs={'class': 'calendardate'})
                try:
                    url_suffix = date_element.contents[0].attrs['name'] # 'mar10'
                except Exception as ex:
                    print(f'Unable to parse URL suffix for event {event_title}')
                    continue
                try:
                    date_time_text = str(date_element.contents[1])  # 'March 10 • Saturday, 6 pm '
                except Exception as ex:
                    print(f'Unable to parse date/time text for event {event_title}')
                    continue
                day_of_month = int(re.search('([0-9]{1,2})', date_time_text).groups()[0])
                try:
                    event_date = date(year=first_of_month.year, month=first_of_month.month, day=day_of_month)
                except Exception as ex:
                    raise
                if event_date <= date.today():
                    continue
                event_time_text = re.search('([0-9]{1,2} (am|pm)) *$', date_time_text).groups()[0] # 6 pm
                event_time = datetime.strptime(event_time_text, '%I %p')
                event_dt = datetime.combine(event_date, event_time.time())
                set_start_end_fields_from_start_dt(csv_dict, event_dt)
                csv_dict['event_dt'] = event_dt

                # Price
                price_line = [line for line in event_lines if '$' in line][0]
                event_lines = [line for line in event_lines if not '$' in line]
                price = parse_price_range(price_line)
                csv_dict['event_cost'] = price
                if price == '0' or not price:
                    event_tags.append('Free')

                # Event description
                event_description_rows = event_lines[:]
                event_description_rows.append('')
                event_description_rows.append('<b>Performers</b>')
                event_description_rows += main_artists
                event_description_rows += sub_artists
                csv_dict['event_description'] = '\r\n'.join(event_description_rows)

                # Event tags
                parse_event_tags(csv_dict, event_tags,' '.join(event_lines + main_artists + sub_artists))

                # Fill in remaining event dictionary
                relevant = not not piano_artists
                if not relevant:
                    continue
                csv_dict['relevant'] = True
                csv_dict['event_website'] = 'http://bargemusic.org/calendar.html#{0}'.format(url_suffix)
                csv_dict['event_tags'] = ','.join(event_tags)
                csv_dict['external_image_url'] = 'http://bargemusic.org/images/logo-home.jpg'
                csv_rows.append(csv_dict)

                print("Parsed '{0}' '{1}'. Tags: {2}. Cost: {3}" \
                      .format(csv_dict["start_date"], csv_dict["event_name"],
                            csv_dict["event_tags"], csv_dict.get("event_cost")))

        csv_rows.sort(key=lambda r: r['event_dt'])
        for row in csv_rows:
            print("Parsed '{0}' '{1}'. Tags: {2}. Cost: {3}" \
                  .format(row["start_date"], row["event_name"],
                          row["event_tags"], row.get("event_cost")))

        return csv_rows
