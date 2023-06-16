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
    sleep(0.15)
    headers = {"User-Agent": ua.random, "Accept-Encoding":"gzip, deflate", "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT":"1","Upgrade-Insecure-Requests":"1", "allow_redirects":"False"}   
    e = Extractor.from_yaml_file('selectors.yml')

    # Download the page using requests
    try:
        r = requests.get(url, headers)
    except Exception:
        sleep(10)
        print("issues with " + url)
        return e.extract("")

    # Pass the HTML of the page and create
    return e.extract(r.text)

#, open('data.csv','w', encoding="utf-8") as outfile
with open("urls.txt",'r', encoding="utf-8") as urlList, open('finals.csv','w+', encoding="utf-8") as res:
    res.write("recent rating, immediate rating, bottom, claim rating, rating #, link, title\n")
    num = 0
    for url in urlList.readlines():
        num += 1
        total, complete, i, l, half, lowest, passed, dp, list = 0.0, 0.0, 1, 0, 0, 50.0, True, False, []
        
        fixed = url[:len(url) - 1]
        id = url[39:49]
        if "/dp/" in url:
            id = re.search('/dp/(.*?)/', url).group(1)
            dp = True
            fixed = "https://www.amazon.com/product-reviews/" + id + "/?pageNumber=1&reviewerType=avp_only_reviews&sortBy=recent"
        print("Downloading %s, "%id+str(num))
        
        while i < 11:
            if l > 9:
                passed = False
                res.write(" failed to download " + fixed + "\n")
                break
            data = scrape(fixed)
            try:
                # see dif print(len(data['reviews']))
                if data:
                    for r in data['reviews']:
                        print(".")
                        list.append(float(r['rating'].split(' out of')[0]))
                        print(".")
                        total += list[-1]
                        complete += list[-1]
                        
                        if len(data['reviews']) < 10:
                            i = 11
                            passed = False
                            break
                        
                        if len(list) == 10:
                            total -= list.pop(0)
                            if total < limiter:
                                i = 11
                                passed = False
                                break
                            if total < lowest:
                                lowest = total           
                    print(".")
                    fixed = 'https://www.amazon.com'+data['next_page']
                    #print(fixed)
                    i += 1
            except TypeError as te:
                print('Retrying page ' + str(i))
                print(fixed)
                sleep(10)
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
