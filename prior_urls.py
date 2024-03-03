from pathlib import Path


# Append a list of URLs to the end of a file
# This is done when we are saving the csv file for uploading to the website
def append_to_prior_urls_file(urls: list[str], file_name: str) -> None:
    # Read the existing URLs from the file
    existing_urls = _read_urls_from_file(file_name)

    # Combine the existing URLs with the new URLs
    all_urls = sorted(list(set(existing_urls + urls)))

    # Strip whitespace from the URLs
    all_urls = [url.strip() for url in all_urls if url.strip()]

    # Write the URLs to the file
    prior_file_name = _create_prior_file_name(file_name)
    with open(prior_file_name, "w") as f:
        for url in all_urls:
            f.write(url + "\n")


# Take a list of URLs and remove ones that are already in the file
# This is done when we are about to scrape websites and want to avoid scraping URLs we have already scraped
def remove_existing_urls(urls: list[str], file_name: str) -> list[str]:
    existing_urls = _read_urls_from_file(file_name)
    return sorted(list(set(urls) - set(existing_urls)))


# Read a list of URLs from a file
def _read_urls_from_file(file_name: str) -> list[str]:
    prior_file_name = _create_prior_file_name(file_name)

    try:
        with open(prior_file_name, "r") as f:
            return [l.strip() for l in f.readlines()]
    except FileNotFoundError:
        return []


# Create a prior file name based on an input file name
# The new name will be the input file name with the word "prior" inserted before the file extension
def _create_prior_file_name(file_name: str) -> str:
    path = Path(file_name)
    prior_file_name = path.with_name(f"{path.stem}.prev{path.suffix}")
    return str(prior_file_name)
