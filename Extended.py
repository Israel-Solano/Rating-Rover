from selectorlib import Extractor
import requests 
from time import sleep
import csv
import requests
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from time import sleep

#Uncomment if you would prefer to input at execution 
#url = input("Enter the url of your best-seller page:")
url ="https://www.amazon.com/Best-Sellers-Amazon-Devices-Accessories/zgbs/amazon-devices/ref=zg_bs_nav_0"

headers ={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0", "Accept-Encoding":"gzip, deflate", "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT":"1","Connection":"close", "Upgrade-Insecure-Requests":"1"}

chrome_options = Options()
chrome_options.headless = True
driver = webdriver.Chrome(options=chrome_options)
actions = ActionChains(driver)

def move():
    i = 0
    while i < 5:
        el = driver.find_element(By.CLASS_NAME, "a-pagination")
        action = ActionChains(driver)
        action.move_to_element(el)
        action.perform()
        sleep(0.2)
        i += 1
    sleep(1)

driver.implicitly_wait(10) # probably unnecessary, just makes sure all pages you visit fully load
driver.get(url)
move()
HTML = str(driver.page_source.encode("utf-8"))
driver.get(url+"/ref=zg_bs_pg_2?_encoding=UTF8&pg=2")
move()
HTML += str(driver.page_source.encode("utf-8"))
driver.quit()

with open("bestseller.html","w", encoding="utf-8") as f:
    f.write(HTML)

with open('bestseller.html', "r", encoding="utf-8") as infile, open('urls.txt', 'w', encoding="utf-8") as outfile:
    for line in infile:
        result = re.search('of 5 stars" href=(.*)</script>', line)
        if result != None:
            newest = re.findall('-reviews(.*?)ref', result.string)
            outfile.write('https://www.amazon.com/product-reviews')
            outfile.write('?pageNumber=1&reviewerType=avp_only_reviews&sortBy=recent\nhttps://www.amazon.com/product-reviews'.join(newest))
            outfile.write('?pageNumber=1&reviewerType=avp_only_reviews&sortBy=recent\n')

# Create an Extractor by reading from the YAML file
e = Extractor.from_yaml_file('selectors.yml')

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

with open("urls.txt",'r', encoding="utf-8") as urllist, open('data.csv','w', encoding="utf-8") as outfile, open('finals.csv','w', encoding="utf-8") as res:
    writer = csv.DictWriter(outfile, fieldnames=["title","date","variant","rating","product","url"],quoting=csv.QUOTE_ALL)
    writer.writeheader()
    num = 0
    for url in urllist.readlines():
        list = []
        total, complete, i, l= 0.0, 0.0, 1.0, 0
        passed = True
        fixed = url[:len(url) - 1]
        num += 1
        print("Downloading %s, "%fixed+str(num))
        while i < 6:
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
                        if len(list) == 10:
                            total -= list.pop(0)
                            if total <= 34 or len(data['reviews']) < 10:
                                i = 6
                                passed = False
                                break
                    fixed = 'https://www.amazon.com'+data['next_page']
                    i += 1
            except TypeError as te:
                print('fuck')
                sleep (1)
                l += 1
            except AttributeError as huh:
                passed = False
                print('why')
                break
            
        if passed:
            res.write(fixed+", "+str(complete)+", "+str(complete/50)+", "+str(num)+"\n")
                    
        sleep(5)