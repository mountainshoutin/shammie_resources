# shammie_resources

Script to take in users input as a full URL, EG. https://example.com in comma separated format. 
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
