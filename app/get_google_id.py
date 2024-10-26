import requests
import re

def is_short_url(url):
    # Check if the URL is a short Google Maps URL based on known patterns
    return 'goo.gl' in url or 'maps.app.goo.gl' in url

def expand_short_url(short_url):
    # Send a request to the short URL to get the long URL
    response = requests.get(short_url)
    # Check if the request was successful
    if response.status_code == 200:
        # Get the long URL from the response
        long_url = response.url
        return long_url
    else:
        print("Failed to expand URL")
        return None

def extract_google_id(long_url):
    # Use a regular expression to extract the Google ID from the long URL
    match = re.search(r'1s([^!]+)', long_url)  # Adjust regex to capture until the next '!'
    if match:
        google_id = match.group(1)  # Get the complete google_id
        return google_id
    else:
        print("Google ID not found in the URL")
        return None

def process_url(url):
    if is_short_url(url):
        google_id = ""
        long_url = expand_short_url(url)
        if long_url:
            print("Expanded URL:", long_url)
            google_id = extract_google_id(long_url)
            if google_id:
                print("Google ID:", google_id)
    else:
        print("Processing long URL...")
        google_id = extract_google_id(url)
        if google_id:
            print("Google ID:", google_id)
    return google_id