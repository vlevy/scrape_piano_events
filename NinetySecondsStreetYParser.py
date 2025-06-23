import datetime as dt
import logging
import re

import bs4

from EventParser import EventParser
from parser_common_code import (
    initialize_csv_dict,
    parse_event_tags,
    set_start_end_fields_from_start_dt,
    title_caps,
)

logger = logging.getLogger(__name__)

TIMEZONE_SUFFIX = re.compile(r"\s*[A-Z]{2,4}\s*$")  # trims “ ET”, “ PT”, etc.


class NinetySecondStreetYParser(EventParser):
    def extract_event_datetimes(self, soup: bs4.BeautifulSoup) -> list[dt.datetime]:
        events: list[dt.datetime] = []
        current_year = dt.datetime.now().year

        for arrangement in soup.select(".pdp-hero__arrangement"):
            month_el = arrangement.select_one(".pdp-hero__month")
            day_el = arrangement.select_one(".pdp-hero__date")
            time_el = arrangement.select_one(".pdp-hero__time")
            if not (month_el and day_el and time_el):
                continue

            month = month_el.get_text(strip=True)
            day = day_el.get_text(strip=True)
            raw_time = time_el.get_text(strip=True)
            clean_time = TIMEZONE_SUFFIX.sub("", raw_time)  # remove trailing timezone

            fmt = "%b %d %Y %I:%M %p" if ":" in clean_time else "%b %d %Y %I %p"
            try:
                start_dt = dt.datetime.strptime(
                    f"{month} {day} {current_year} {clean_time}", fmt
                )
                if start_dt < dt.datetime.now():
                    start_dt = start_dt.replace(year=current_year + 1)
                events.append(start_dt)
            except ValueError:
                pass

        return events

    def parse_soup_to_event(self, url, soup):
        # -----------------------------------
        # Easy fields
        # -----------------------------------
        csv_dict = initialize_csv_dict(url)
        event_tags = ["Classical"]
        csv_dict["event_website"] = url
        csv_dict["venue_name"] = "92nd Street Y"

        # -------------------------------------------------
        # Event title
        # -------------------------------------------------
        title_el = (
            soup.select_one(
                'meta[property="og:title"]'
            )  # Open‑Graph tag (first choice)
            or soup.select_one(".pdp-hero__title")  # In‑page hero heading (fallback)
        )
        title: str = (
            title_el["content"].strip()
            if title_el and title_el.has_attr("content")
            else title_el.get_text(strip=True)
            if title_el
            else ""
        )
        if not title:
            raise ValueError(f"No title found for {url}")
        title = title_caps(title)
        title = f"{title}, at 92nd Street Y"
        csv_dict["event_name"] = title

        # -------------------------------------------------
        # Hero / header image URL
        # -------------------------------------------------
        img_el = soup.select_one(
            ".pdp-hero__images source[media]"
        )  # first responsive <source>
        if not img_el:  # fallback: the img itself
            img_el = soup.select_one(".pdp-hero__images img")

        image_url: str = (
            img_el["srcset"].split()[0]  # take the URL part of "srcset"
            if img_el and img_el.has_attr("srcset")
            else img_el["src"].strip()  # plain src attribute
            if img_el
            else ""
        )
        if image_url.startswith("//"):  # scheme‑relative URL
            image_url = "https:" + image_url
        image_url: str = image_url.split("?", 1)[0]
        csv_dict["external_image_url"] = image_url

        # -------------------------------------------------
        # Event date / time list  →  List[datetime]
        # -------------------------------------------------
        event_datetimes = self.extract_event_datetimes(soup)

        if event_datetimes:
            set_start_end_fields_from_start_dt(csv_dict, event_datetimes[0])
        else:
            logger.error(f"No event datetimes found for {url}")
            event_tags.append("Recurring")

        # -------------------------------------------------
        # Body / overview text
        # -------------------------------------------------
        overview_paras = soup.select(".pdp-overview p")  # every <p> inside overview
        body_text: str = "\n\n".join(p.get_text(strip=True) for p in overview_paras)
        csv_dict["event_description"] = body_text

        # -------------------------------------------------
        # Cost
        # -------------------------------------------------
        prices = []

        # Extract all price elements
        for price_div in soup.select(".pdp-hero__price"):
            try:
                price = float(price_div["data-min"])
                prices.append(price)
            except ValueError:
                logger.warning(f"Invalid price found for {url}: {price_div}")
                prices = []
                break

        if prices:
            min_price = min(prices)
            max_price = max(prices)
            if min_price == max_price:
                csv_dict["event_cost"] = f"{min_price:.2f}"
            else:
                csv_dict["event_cost"] = f"{min_price:.2f}-{max_price:.2f}"
        else:
            logger.warning(f"No prices found for {url}")

        # -------------------------------------------------
        # Event tags
        # -------------------------------------------------
        # Event tags
        if len(event_datetimes) > 0:
            event_tags.append("Recurring")
        event_text = "\n".join((csv_dict["event_name"], csv_dict["event_description"]))
        parse_event_tags(csv_dict, event_tags, event_text)
        csv_dict["event_tags"] = ",".join(event_tags)

        return csv_dict
