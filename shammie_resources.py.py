import whois
import socket
from pyppeteer import launch
import tldextract
import asyncio


async def get_requested_domains(url):
    browser = await launch(headless=False)
    page = await browser.newPage()
    requested_domains = set()
    def request_handler(request):
        domain = tldextract.extract(request.url).registered_domain
        if domain:
            requested_domains.add(domain)
    page.on('request', request_handler)

    await page.setExtraHTTPHeaders({
        'Accept-Language': 'en-US,en;q=0.9'
    })
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36')
    await page.goto(url, {'waitUntil': 'networkidle2'})
    await browser.close()
    return requested_domains


async def main():
    user_input = input("Enter full website URLs (comma-separated, including 'http://' or 'https://'): ")
    urls = [url.strip() for url in user_input.split(',')]
    all_domains = set()

    for url in urls:
        try:
            requested_domains = await get_requested_domains(url)
            all_domains.update(requested_domains)
        except Exception as e:
            print(f"Error browsing {url}: {str(e)}")

    with open('child_domains.txt', 'w') as f:
        for domain in all_domains:
            f.write(domain + '\n')

    with open('whois_data.txt', 'w') as f:
        for url in urls:
            try:
                domain = tldextract.extract(url).registered_domain
                whois_data = whois.whois(domain)
                f.write(str(whois_data) + '\n\n')
            except Exception as e:
                print(f"Error fetching whois data for {url}: {str(e)}")

    with open('unbound_includes.conf', 'w') as f:
        for domain in all_domains.union(urls):
            try:
                ip_addresses = socket.getaddrinfo(domain, None, family=socket.AF_INET)
                for ip_address in ip_addresses:
                    f.write(f"local-data: \"{domain} A {ip_address[4][0]}\"\n")
            except Exception as e:
                print(f"Error fetching IP address for {domain}: {str(e)}")


if __name__ == '__main__':
    asyncio.run(main())
