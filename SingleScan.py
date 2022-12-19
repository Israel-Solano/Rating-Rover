from selectorlib import Extractor
import requests 
from time import sleep
import csv
import re

#Uncomment if you would prefer to write in your best seller category url
url = input("Enter the url of your product page:")
#url ="https://www.amazon.com/Best-Sellers-Home-Kitchen-Household-Tower-Fans/zgbs/home-garden/241127011/ref=zg_bs_nav_home-garden_3_3737631"

headers ={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0", "Accept-Encoding":"gzip, deflate", "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT":"1","Connection":"close", "Upgrade-Insecure-Requests":"1"}


# Create an Extractor by reading from the YAML file
e = Extractor.from_yaml_file('selectors.yml')

# Download the page using requests
def scrape(url):  

    headers = {'dnt': '1', 'upgrade-insecure-requests': '1', 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'navigate', 'sec-fetch-user': '?1', 'sec-fetch-dest': 'document', 'referer': 'https://www.amazon.com/', 'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',}

    # Download the page using requests
    r = requests.get(url, headers=headers)
    # Simple check to check if page was blocked (Usually 503)
    if r.status_code > 500:
        if "To discuss automated access to Amazon data please contact" in r.text:
            print("Page %s was blocked by Amazon. Please try using better proxies\n"%url)
        else:
            print("Page %s must have been blocked by Amazon as the status code was %d"%(url,r.status_code))
        return None
    # Pass the HTML of the page and create 
    return e.extract(r.text)

with open('Data/data.csv','w', encoding="utf-8") as outfile:
    writer = csv.DictWriter(outfile, fieldnames=["title","date","variant","rating","product","url"],quoting=csv.QUOTE_ALL)
    writer.writeheader()
    list = []
    total, complete, i, l, half= 0.0, 0.0, 1.0, 0, 0
    passed = True
    #url = url[:len(url) - 1]
    temp = re.search('/dp/(.*)/', url).group(1)
    fixed = ('http://amazon.com/product-reviews/'+temp+'/ref=cm_cr_arp_d_viewopt_srt?ie=UTF8&reviewerType=avp_only_reviews&pageNumber=1&sortBy=recent')
    print(fixed)
    while i < 11:
        #print("Downloading %s, "%fixed+str(i))
        if l > 9:
            passed = False
            break
        data = scrape(fixed)
        try:
            # see dif print(len(data['reviews']))
            if data:
                for r in data['reviews']:
                    r["product"] = data["product_title"]
                    r['url'] = fixed
                    r['rating'] = r['rating'].split(' out of')[0]
                    writer.writerow(r)
                    
                    list.append(float(r['rating']))
                    total += list[-1]
                    complete += list[-1]

                    if len(data['reviews']) < 10:
                        i = 11
                        passed = False
                        break

                    if len(list) == 10:
                        total -= list.pop(0)
                        if total <= 30:
                            i = 11
                            passed = False
                            break
                fixed = 'https://www.amazon.com'+data['next_page']
                print(fixed)
                i += 1
        except TypeError as te:
            print('Retrying')
            sleep (1)
            l += 1
        except AttributeError as huh:
            passed = False
            print('Too few')
            break
        if(i == 6):
            half = complete    
    if passed:
        print(str(complete/100)+", "+str(half/50)+", "+"https://www.amazon.com/dp/"+temp+"\n")
                