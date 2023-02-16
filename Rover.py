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

#url = input("Enter the url of your best-seller page:")
#Uncomment if you would prefer to write in your best seller category url
url = 'https://www.amazon.com/Best-Sellers-Adult-Electric-Bicycles/zgbs/sporting-goods/3405141'

headers ={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0", "Accept-Encoding":"gzip, deflate", "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT":"1","Connection":"close", "Upgrade-Insecure-Requests":"1"}

chrome_options = Options()
chrome_options.headless = True
driver = webdriver.Chrome(options=chrome_options)
actions = ActionChains(driver)

#move to bottom so it can get the rest of the page
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

url = url.split('/ref=')[0]
driver.implicitly_wait(10) # probably unnecessary, just makes sure all pages you visit fully load
driver.get(url) #Something about get bothers it
move()
HTML = str(driver.page_source.encode("utf-8"))
driver.get(url+"/ref=zg_bs_pg_2?_encoding=UTF8&pg=2")
move()
HTML += str(driver.page_source.encode("utf-8"))
driver.quit()

#add the data you got to a file
with open("bestseller.html","w+", encoding="utf-8") as f:
    f.write(HTML)

line = ""
with open('bestseller.html', "r", encoding="utf-8") as inFile, open('urls.txt', 'w+', encoding="utf-8") as outfile:
    line = inFile.readline()
    newest = re.findall('-reviews(.*?)ref', line)
    outfile.write('https://www.amazon.com/product-reviews')
    outfile.write('?pageNumber=1&reviewerType=avp_only_reviews&sortBy=recent\nhttps://www.amazon.com/product-reviews'.join(newest))
    outfile.write('?pageNumber=1&reviewerType=avp_only_reviews&sortBy=recent\n')

ua = fake_useragent.UserAgent()
# Create an Extractor by reading from the YAML file

def scrape(url):  
    sleep(0.1)
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
with open("urls.txt",'r', encoding="utf-8") as urlList, open('finals.csv','w+', encoding="utf-8") as res:
    category = str(re.search('text-bold">Best Sellers in (.*?)</', line).group(1))
    top = category + ", " + url+"\n"
    res.write(top)
    print(top)
    pieces = line.split('class="a-icon-alt')
    #res.write("ranking, price, recent rating, immediate rating, bottom, claim rating, rating #, link, title\n")
    # writer = csv.DictWriter(outfile, fieldnames=["title","date","variant","rating","product","url"],quoting=csv.QUOTE_ALL).writeheader()
    num = 0
    for url in urlList.readlines():
        num += 1
        total, complete, i, l, half, lowest, passed , list = 0.0, 0.0, 1.0, 0, 0, 50.0, True, []
        fixed = url[:len(url) - 1]
        id = url[39:49]
        print("Downloading %s, "%id+str(num))

        try:
            sleep(0.1)
            checkNum = str(re.search('total ratings, (.*?) with reviews', str(requests.get(url, headers=headers).content)).group(1)).replace(",", "")
            if int(checkNum) < 101:
                print('Only ' + checkNum+' reviews\n')
                continue
        
        except AttributeError as e:
            print('Review Number Error')
            continue
        
        while i < 11:
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
                            if total < 30:
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
            part1 = pieces[num - 1].split('img alt=')[-1]
            title = re.search('"(.*?)" src="https', part1).group(1).replace(",","").replace("\\x","")
            titStar = re.search('">(.*?) out of', pieces[num]).group(1)
            starNum = re.search('class="a-size-small">(.*?)</span>', pieces[num]).group(1).replace(",","")
            try:
                result = re.search('\$(.*?)</spa', pieces[num]).group(1).replace(",","")
            except AttributeError as huh:
                result = "N/A"
            message = "%d, $%s, %.2f, %.2f, %d, %s, %s, https://www.amazon.com/dp/%s/, %s\n"%(num, result,complete/100, half/50, lowest, titStar, starNum, id, title)
            res.write(message)
            print(message)