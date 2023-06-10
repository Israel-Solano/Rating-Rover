from time import sleep
import os
import re
from selectorlib import Extractor
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
import fake_useragent


if __name__ == "__main__":
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    os.chdir(curr_dir)

def move(driver):
    i = 0
    sleep(5)
    while i < 5:
        el = driver.find_element(By.CLASS_NAME, "a-pagination")
        action = ActionChains(driver)
        action.move_to_element(el)
        action.perform()
        sleep(0.2)
        i += 1
        
def get_page_source(driver, url, output_text):
    m, html = False, ""
    while not m:
        try:
            driver.get(url)
            move(driver)
            html = str(driver.page_source.encode("utf-8"))
            m = True
        except Exception:
            output_text.insert("end", 'Damaged, trying again...\n')
            output_text.update()
            sleep(10)
    return html

def scrape(url):
    sleep(0.15)
    e = Extractor.from_yaml_file('selectors.yml')

    # Download the page using requests
    try:
        r = requests.get(url, headers=get_headers())
    except Exception:
        sleep(10)
        print("issues with " + url)
        return e.extract("")

    # Pass the HTML of the page and create
    return e.extract(r.text)

def get_headers():
    ua = fake_useragent.UserAgent()
    headers = {
        "User-Agent": ua.random,
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "DNT": "1",
        "Connection": "close",
        "Upgrade-Insecure-Requests": "1"
    }
    return headers

def initialize_driver():
    chrome_options = Options()
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument("--headless")
    return webdriver.Chrome(options=chrome_options)

def bestseller_filing(HTML):
        with open("bestseller.html","w+", encoding="utf-8") as f:
            f.write(HTML)
        with open('bestseller.html', "r", encoding="utf-8") as inFile, open('urls.txt', 'w+', encoding="utf-8") as outfile:
            line = inFile.readline()
            outfile.write('https://www.amazon.com/product-reviews')
            outfile.write('?pageNumber=1&reviewerType=avp_only_reviews&sortBy=recent\nhttps://www.amazon.com/product-reviews'.join(re.findall('-reviews(.*?)ref', line)))
            outfile.write('?pageNumber=1&reviewerType=avp_only_reviews&sortBy=recent\n')
            return line
            
def scrape_site(output_text, url, limiter):
    url = url.split('/ref=')[0]
    driver = initialize_driver()
    actions = ActionChains(driver)
    output_text.insert("end", "Getting first listings...\n")
    output_text.update()
    HTML = get_page_source(driver, url, output_text)
    output_text.insert("end", "Getting last listings...\n")
    output_text.update()
    HTML += get_page_source(driver, url+"/ref=zg_bs_pg_2?_encoding=UTF8&pg=2", output_text)
    driver.quit()
    #add the data you got to a file
    line = bestseller_filing(HTML)

    with open("urls.txt",'r', encoding="utf-8") as urlList, open('finals.csv','w+', encoding="utf-8") as res:
        category = str(re.search('text-bold">Best Sellers in (.*?)</', line).group(1))
        pieces = line.split('class="a-icon-alt')
        top = "%s, %d results\n"%(category, len(pieces))
        res.write(top)
        output_text.insert("end", "\n%s" % top)
        output_text.update()
        #res.write("ranking, price, recent rating, immediate rating, bottom, claim rating, rating #, link, title\n")
        # writer = csv.DictWriter(outfile, fieldnames=["title","date","variant","rating","product","url"],quoting=csv.QUOTE_ALL).writeheader()
        num, data_list = 0, []
        total_urls = sum(1 for _ in urlList)
        urlList.seek(0)  # Reset file pointer to the beginning
        
        for url in urlList.readlines():
            num += 1
            total, complete, i, l, half, lowest, passed , list= 0.0, 0.0, 1, 0, 0, 50.0, True, []
            fixed = url[:len(url) - 1]
            id = url[39:49]
            
            while l < 10:
                try:
                    first = scrape(fixed)["review_count"]
                    checkNum = str(re.search(', (.*?) with', first).group(1)).replace(",", "")
                    if int(checkNum) < 101:
                        passed = False
                        i = 11
                    break
                except TypeError as e:
                    output_text.insert("end", 'Review Number Error\n')
                    output_text.update()
                    l += 1
                    
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
                            list.append(float(r['rating'].split(' out of')[0]))
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
                        fixed = "https://www.amazon.com/product-reviews/" + id + "/?pageNumber=" + \
                            str(i + 1) + "&reviewerType=avp_only_reviews&sortBy=recent"
                        #print(fixed)
                        i += 1
                except TypeError as te:
                    output_text.insert("end", 'Retrying page ' + str(i) + " from listing #" + str(num) + "\n")
                    output_text.update()
                    sleep(10 + i)
                    l += 1
                except AttributeError as huh:
                    passed = False
                    break
                if(i == 6):
                    half = complete    
            if passed:
                #possibly add .split('</span></div></a></div><div class="zg-mlt-list-type aok-hidden">')[-1]
                title = re.sub(r'[^\x00-\x7F]+', '', data["product_title"]).replace(",","")
                titStar = data["rating"].split(' out of')[0]
                starNum = data["starNum"].split(' global ratings')[0].replace(",","")
                try:
                    result = re.search('\$(.*?)</spa', pieces[num]).group(1).replace(",","")
                except AttributeError as huh:
                    result = "N/A"
                message = "%d, $%s, %.2f, %.2f, %d, %s, %s, https://www.amazon.com/dp/%s/, %s\n"%(num, result, complete/100, half/50, lowest, titStar, starNum, id, title)
                res.write(message)
                data_list.append([num, result, complete / 100, half / 50, lowest, titStar, int(starNum), "https://www.amazon.com/dp/%s/"%id, title])
                #result left
    # Sort the data by "Starnum" in descending order
    return sorted(data_list, key=lambda x: (x[6]), reverse=True), category
