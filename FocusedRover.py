from selectorlib import Extractor
import requests 
from time import sleep
import csv
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
import os
import fake_useragent

if __name__ == "__main__":
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    os.chdir(curr_dir)
ua = fake_useragent.UserAgent()
# Create an Extractor by reading from the YAML file


def scrape(url):  
    e = Extractor.from_yaml_file('selectors.yml')
    headers = {'dnt': '1', 'upgrade-insecure-requests': '1', 'user-agent': ua.random,
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'navigate', 'sec-fetch-user': '?1', 'sec-fetch-dest': 'document', 'referer': 'https://www.amazon.com/', 'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',}

    # Download the page using requests
    try:
        r = requests.get(url, headers=headers)
    except Exception:
        sleep(5)
        print("issues")
        return e.extract("")
    # Simple check to check if page was blocked (Usually 503)
    if r.status_code > 500:
        if "To discuss automated access to Amazon data please contact" in r.text:
            print("Page %s was blocked by Amazon. Please try using better proxies\n"%url)
        else:
            print("Page %s must have been blocked by Amazon as the status code was %d"%(url,r.status_code))
        return None
    # Pass the HTML of the page and create 
    return e.extract(r.text)

#, open('data.csv','w', encoding="utf-8") as outfile
with open("urls.txt",'r', encoding="utf-8") as urlList, open('finals.csv','w+', encoding="utf-8") as res:
    res.write("recent rating, immediate rating, bottom, claim rating, rating #, link, title\n")
    num = 0
    for url in urlList.readlines():
        num += 1
        total, complete, i, l, half, lowest, passed, dp, list = 0.0, 0.0, 1.0, 0, 0, 50.0, True, False, []
            
        
        fixed = url[:len(url) - 1]
        id = url[39:49]
        if "/dp/" in url:
            id = re.search('/dp/(.*?)/', url).group(1)
            dp = True
            fixed = "https://www.amazon.com/product-reviews/" + id + "/?pageNumber=1&reviewerType=avp_only_reviews&sortBy=recent"
        elif "/gp/" in url: 
            id = re.search('/gp/product/(.*?)/', url).group(1)
            dp = True
            fixed = "https://www.amazon.com/product-reviews/" + id + "/?pageNumber=1&reviewerType=avp_only_reviews&sortBy=recent"
        
        print("Downloading %s, "%fixed+str(num))

        headers ={"User-Agent":ua.random, "Accept-Encoding":"gzip, deflate", "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT":"1","Connection":"close", "Upgrade-Insecure-Requests":"1"}
        try:
            sleep(0.15)
            checkNum = str(re.search(', (.*?) with', scrape(fixed)["review_count"]).group(1)).replace(",", "")
            if int(checkNum) < 101:
                print('Only ' + checkNum+' reviews\n')
                continue
        
        except AttributeError as e:
            print('Review Number Error')
            continue
        
        while i < 11:
            sleep(0.15)
            if l > 9:
                passed = False
                break
            data = scrape(fixed)
            try:
                # see dif print(len(data['reviews']))
                if data:
                    for r in data['reviews']:
                        list.append(float(r['rating'].split(' out of')[0]))
                        total += list[-1]
                        complete += list[-1]

                        if len(data['reviews']) < 10:
                            i = 11
                            passed = False
                            break

                        if len(list) == 10:
                            total -= list.pop(0)
                            if total < 15:
                                print('Failed on page: ' + str(i) + '\n')
                                i = 11
                                passed = False
                                break
                            if total < lowest:
                                lowest = total        
                    fixed = 'https://www.amazon.com'+data['next_page']
                    #print(fixed)
                    i += 1
            except TypeError as te:
                print('Retrying page ' + str(i))
                sleep (1)
                l += 1
            except AttributeError as huh:
                passed = False
                print('Too few on page ' + str(i))
                break
            if(i == 6):
                half = complete    
        if passed:
            #possibly add .split('</span></div></a></div><div class="zg-mlt-list-type aok-hidden">')[-1]
            title = re.sub(r'[^\x00-\x7F]+', '', data["product_title"]).replace(",","")
            titStar = data["rating"].split(' out of')[0]
            starNum = data["starNum"].split(' global ratings')[0].replace(",","")
            
            if dp:
                message = "%.2f, %.2f, %d, %s, %s, %s, %s\n"%(complete/100, half/50, lowest, titStar, starNum, fixed, title)
            else:
                message = "%.2f, %.2f, %d, %s, %s, https://www.amazon.com/dp/%s/, %s\n"%(complete/100, half/50, lowest, titStar, starNum, id, title)
            res.write(message)
            print(message)