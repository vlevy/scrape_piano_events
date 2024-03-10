def clean_up_url(url: str) -> str:
    """Clean up a URL by removing whitespace and trailing slashes

    Args:
        url: A URL

    Returns:
        A cleaned up URL
    """
    return url.strip().removesuffix("/")


def clean_up_urls(urls: list[str]) -> list[str]:
    """Clean up URLs by removing whitespace and trailing slashes

    Args:
        urls (list[str]): A list of URLs

    Returns:
        list[str]: A list of cleaned up URLs
    """
    return [clean_up_url(url) for url in urls if url.strip()]
