import whois
import socket
import tldextract
import asyncio
from pyppeteer import launch

async def get_requested_domains(url):
    # Launch a new browser instance
    browser = await launch(headless=False)
    # Create a new page instance
    page = await browser.newPage()
    # Set up a request handler to intercept and extract the domains requested by the page
    requested_domains = set()
    def request_handler(request):
        # Use tldextract to extract the registered domain from the request URL
        domain = tldextract.extract(request.url).registered_domain
        if domain:
            # Add the domain to the set of requested domains
            requested_domains.add(domain)
    page.on('request', request_handler)

    # Set up the page with headers, user agent, and navigate to the specified URL
    await page.setExtraHTTPHeaders({
        'Accept-Language': 'en-US,en;q=0.9'
    })
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36')
    await page.goto(url, {'waitUntil': 'networkidle2'})
    # Close the browser instance
    await browser.close()
    return requested_domains

async def main():
    # Get website URLs from user input and split into a list
    user_input = input("Enter full website URLs (comma-separated, including 'http://' or 'https://'): ")
    urls = [url.strip() for url in user_input.split(',')]
    # Create a set to hold all domains, including those requested by the given websites
    all_domains = set()

    # Loop through each URL and extract the requested domains from each page
    for url in urls:
        try:
            requested_domains = await get_requested_domains(url)
            all_domains.update(requested_domains)
        except Exception as e:
            print(f"Error browsing {url}: {str(e)}")

    # Write the list of requested domains to a file
    with open('child_domains.txt', 'w') as f:
        for domain in all_domains:
            f.write(domain + '\n')

    # Loop through each URL and retrieve whois data
    with open('whois_data.txt', 'w') as f:
        for url in urls:
            try:
                # Extract the registered domain from the URL and retrieve whois data for that domain
                domain = tldextract.extract(url).registered_domain
                whois_data = whois.whois(domain)
                # Write the whois data to a file
                f.write(str(whois_data) + '\n\n')
            except Exception as e:
                print(f"Error fetching whois data for {url}: {str(e)}")

    # Write the IP address information for all domains to an unbound include file
    with open('unbound_includes.conf', 'w') as f:
        # Loop through each domain and retrieve IP address information
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

