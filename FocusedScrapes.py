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
    
headers ={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0", "Accept-Encoding":"gzip, deflate", "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT":"1","Connection":"close", "Upgrade-Insecure-Requests":"1"}
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

#, open('Data/data.csv','w', encoding="utf-8") as outfile
with open("Data/urls.txt",'r', encoding="utf-8") as urlList, open('Data/finals.csv','w+', encoding="utf-8") as res:
    #pieces = line.split('class="a-icon-alt')
    #res.write("ranking, price, recent rating, immediate rating, bottom, claim rating, rating #, link, title\n")
    # writer = csv.DictWriter(outfile, fieldnames=["title","date","variant","rating","product","url"],quoting=csv.QUOTE_ALL).writeheader()
    num = 0
    for url in urlList.readlines():
        num += 1
        total, complete, i, l, half, lowest, passed , list = 0.0, 0.0, 1.0, 0, 0, 50.0, True, []
        fixed = url[:len(url) - 1]
        id = url[39:49]
        print("Downloading %s, "%id+str(num))

        checker = str(requests.get(url, headers=headers).content)
        try:
            sleep(0.15)
            checkNum = str(re.search('total ratings, (.*?) with reviews', checker).group(1)).replace(",", "")
            if int(checkNum) < 100:
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
                        r["product"] = data["product_title"]
                        r['url'] = fixed
                        r['rating'] = r['rating'].split(' out of')[0]
                        #writer.writerow(r)
                        
                        list.append(float(r['rating']))
                        total += list[-1]
                        complete += list[-1]

                        if len(data['reviews']) < 10:
                            i = 11
                            passed = False
                            break

                        if len(list) == 10:
                            total -= list.pop(0)
                            if total < 10:
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
            #part1 = pieces[num - 1].split('img alt=')[-1]
            title = re.search('<title>Amazon.com: Customer reviews:(.*?)</title>', checker).group(1).replace(",","").replace("\\x","")
            titStar = re.search('a-icon-alt">(.*?) out of 5', checker).group(1)
            starNum = re.search('secondary">(.*?) global ratings</span>', checker).group(1).replace(",","")
            #try:
            #    result = re.search('\$(.*?)</spa', pieces[num]).group(1).replace(",","")
            #except AttributeError as huh:
            #    result = "N/A"
            message = str(num)+", $"+", "+str(complete/100)+", "+str(half/50)+", "+str(lowest)+", "+str(titStar)+", "+str(starNum)+", "+"https://www.amazon.com/dp/"+id+"/, " + title + "\n"
            res.write(message)
            print(message)