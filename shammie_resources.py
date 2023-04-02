#!/usr/bin/env python3
#----------------------------------------------------------------------------
# Created By: Logan Patterson
# Created Date: 04/02/2023
# Version 1.0
# ---------------------------------------------------------------------------
""" Script to take in users input as a full URL, EG. https://example.com in comma separated format. 
Then, using pyppeteer, browses to the website(s) and strips out any resource domains that the website(s) makes 
the requesting client call out to and writes this to a file called resource_domains.txt. 

Then it does a whois on JUST the requested website(s) and pulls this information down into a .txt file called
whois.txt.

Finally, it pulls takes the requested and resource domains, gets the IP address it connects to via sockets, and 
maps that into a unbounds_include.conf file that then can be easily imported into a running unbounds server.

All files will be created in the working directory the Script is run from, and on a new run it will completely
overwrite any existing files from previous runs. 

Input needs to be in comma separated and in Full URL, example: 
https://example.com,https://example2.com,http://example3.com
"""
# ---------------------------------------------------------------------------

import whois
import socket
import tldextract
import asyncio
from pyppeteer import launch

# Define an asynchronous function where we take the browse to the requested sites
async def get_requested_domains(url):
    # Launch a new browser instance
    browser = await launch(headless=False)
    # Here we Create a new page instance
    page = await browser.newPage()
    # Set up a request handler to intercept and extract the resource domains the 
    # website makes our client call out to after it received the web request
    requested_domains = set()
    # Define a function that will pull out any additionally requested domains (resource domains)
    def request_handler(request):
        # Use tldextract to extract the registered domain from the resource URL
        domain = tldextract.extract(request.url).registered_domain
        if domain:
            # Add the domain to the set of requested domains
            requested_domains.add(domain)
    page.on('request', request_handler)

    # Here we setup chromium to appear with a standard UserAgent and Header, so we hopefully
    # don't get blocked by any anti-bot / scraper controls
    await page.setExtraHTTPHeaders({
        'Accept-Language': 'en-US,en;q=0.9'
    })
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36')
    await page.goto(url, {'waitUntil': 'networkidle2'})
    # Closes the browser instance, so we don't wind up with a ton of processes left
    await browser.close()
    return requested_domains

# Define the asynchronous main function of the script that calls on the above functions, after we
# get the input from the user in comma separated format
async def main():
    # Get website URLs from user input and split into a list
    user_input = input("Enter full website URLs (comma-separated, including 'http://' or 'https://'): ")
    urls = [url.strip() for url in user_input.split(',')]
    # Create a set to hold all domains, including the resource sites requested by the site
    all_domains = set()

    # Loop through each URL and call on get_requested_domains to extract any additonally requested resource domains
    for url in urls:
        try:
            requested_domains = await get_requested_domains(url)
            all_domains.update(requested_domains)
        except Exception as e:
            print(f"Error browsing {url}: {str(e)}")

    # Write the list of resource extracted to a file called resource_domains.txt
    with open('resource_domains.txt', 'w') as f:
        for domain in all_domains:
            f.write(domain + '\n')

    # Loop through each URL (only the ones given by user) and retrieve whois data
    # Store the data in a file called whois.txt
    with open('whois.txt', 'w') as f:
        for url in urls:
            try:
                # Extract the registered domain from the URL and retrieve whois data for that domain
                domain = tldextract.extract(url).registered_domain
                whois_data = whois.whois(domain)
                f.write(str(whois_data) + '\n\n')
            except Exception as e:
                print(f"Error fetching whois data for {url}: {str(e)}")

    # Write the DNS address information for all domains to an unbound include file
    with open('unbound_includes.conf', 'w') as f:
        # Loop through each domain and retrieve IP address information by evaluating what we connect to via sockets
        for domain in all_domains.union(urls):
            try:
                # Retrieve a list of IP addresses associated with the domain
                ip_addresses = socket.getaddrinfo(domain, None, family=socket.AF_INET)
                # Write each IP address to the unbound include file in the correct format
                for ip_address in ip_addresses:
                    f.write(f"local-data: \"{domain} A {ip_address[4][0]}\"\n")
            except Exception as e:
                print(f"Error fetching IP address for {domain}: {str(e)}")

if __name__ == '__main__':
    asyncio.run(main())

