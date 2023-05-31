from selectorlib import Extractor
import requests
from time import sleep
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
import os
import fake_useragent
from tkinter import Tk, Label, Entry, Button, Text, Scrollbar
from tkinter.ttk import Treeview, Progressbar

if __name__ == "__main__":
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    os.chdir(curr_dir)

def scrape_site(url):
    ua = fake_useragent.UserAgent()
    url = url.split('/ref=')[0]
    # Uncomment if you would prefer to write in your best seller category URL
    # url = 'https://www.amazon.com/Best-Sellers-Clothing-Shoes-Jewelry-Womens-Swim-Pants/zgbs/fashion/23709657011/ref=zg_bs_nav_fashion_4_15835971'

    headers = {"User-Agent": ua.random, "Accept-Encoding": "gzip, deflate, br",
               "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT": "1",
               "Connection": "close", "Upgrade-Insecure-Requests": "1"}

    chrome_options, line, m = Options(), "", False
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_argument('--ignore-certificate-errors')  # chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    actions = ActionChains(driver)

    # move to bottom so it can get the rest of the page
    def move():
        i = 0
        sleep(5)
        while i < 5:
            el = driver.find_element(By.CLASS_NAME, "a-pagination")
            action = ActionChains(driver)
            action.move_to_element(el)
            action.perform()
            sleep(0.2)
            i += 1

    output_text.insert("end", "Getting first listings...\n")
    output_text.update()
    while m == False:
        try:
            driver.get(url) #Something about get bothers it
            move()
            HTML = str(driver.page_source.encode("utf-8"))
            m = True
        except Exception as e:
            output_text.insert("end", 'Damaged, trying again...\n')
            output_text.update()
            sleep (10)

    output_text.insert("end", "Getting last listings...\n")
    output_text.update()
    while m == True:
        try:
            driver.get(url+"/ref=zg_bs_pg_2?_encoding=UTF8&pg=2")
            move()
            HTML += str(driver.page_source.encode("utf-8"))
            m = False
        except Exception as e:
            output_text.insert("end", 'Damaged, trying again...\n')
            output_text.update()
            sleep (10)

    driver.quit()

    #add the data you got to a file
    with open("bestseller.html","w+", encoding="utf-8") as f:
        f.write(HTML)

    with open('bestseller.html', "r", encoding="utf-8") as inFile, open('urls.txt', 'w+', encoding="utf-8") as outfile:
        line = inFile.readline()
        outfile.write('https://www.amazon.com/product-reviews')
        outfile.write('?pageNumber=1&reviewerType=avp_only_reviews&sortBy=recent\nhttps://www.amazon.com/product-reviews'.join(re.findall('-reviews(.*?)ref', line)))
        outfile.write('?pageNumber=1&reviewerType=avp_only_reviews&sortBy=recent\n')

    # Create an Extractor by reading from the YAML file

    def scrape(url):  
        sleep(0.25)
        e = Extractor.from_yaml_file('selectors.yml')
        headers = {"User-Agent": ua.random, "Accept-Encoding":"gzip, deflate", "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT":"1","Upgrade-Insecure-Requests":"1", "allow_redirects":"False"}   

        # Download the page using requests
        try:
            r = requests.get(url, headers=headers)
        except Exception:
            sleep(10)
            print("issues with " + url)
            return e.extract("")

        # Pass the HTML of the page and create 
        #print(re.sub(r'[^\x00-\x7F]+', '', r.text))
        return e.extract(r.text)

    with open("urls.txt",'r', encoding="utf-8") as urlList, open('finals.csv','w+', encoding="utf-8") as res:
        category = str(re.search('text-bold">Best Sellers in (.*?)</', line).group(1))
        pieces = line.split('class="a-icon-alt')
        top = "%s, %s, %d results\n"%(category, url,len(pieces))
        res.write(top)
        output_text.insert("end", "\n%s" % top)
        output_text.update()
        #res.write("ranking, price, recent rating, immediate rating, bottom, claim rating, rating #, link, title\n")
        # writer = csv.DictWriter(outfile, fieldnames=["title","date","variant","rating","product","url"],quoting=csv.QUOTE_ALL).writeheader()
        num, data_list = 0, []
        for url in urlList.readlines():
            num += 1
            total, complete, i, l, half, lowest, passed , list= 0.0, 0.0, 1, 0, 0, 50.0, True, []
            fixed = url[:len(url) - 1]
            id = url[39:49]
            output_text.insert("end", "\nDownloading %s, %s\n" % (fixed, str(num)))
            output_text.update()

            while l < 10:
                try:
                    first = scrape(fixed)["review_count"]
                    checkNum = str(re.search(', (.*?) with', first).group(1)).replace(",", "")
                    if int(checkNum) < 101:
                        output_text.insert("end", 'Only ' + checkNum + ' reviews\n')
                        output_text.update()
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
                                if total < 30:
                                    output_text.insert("end", 'Failed on page: ' + str(i) + "\n")
                                    output_text.update()
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
                    output_text.insert("end", 'Retrying page ' + str(i) + "\n")
                    output_text.update()
                    sleep(10)
                    l += 1
                except AttributeError as huh:
                    passed = False
                    output_text.insert("end", 'Too few on page ' + str(i) + "\n")
                    output_text.update()
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
                output_text.insert("end", message)
                output_text.update()# Append the data to the list
                data_list.append([num, result, complete / 100, half / 50, lowest, titStar, starNum, "https://www.amazon.com/dp/%s/"%id, title])
                #result left

    return data_list

def display_results(data, urly):
    # Create the Treeview widget
    treeview = Treeview(window)
    treeview["columns"] = ("#0", "#1", "#2", "#3", "#4", "#5", "#6", "#7")
    treeview.pack()

    # Define the columns
    treeview.heading("#0", text="Result")
    treeview.heading("#1", text="Complete / 100")
    treeview.heading("#2", text="Half / 50")
    treeview.heading("#3", text="Lowest")
    treeview.heading("#4", text="TitStar")
    treeview.heading("#5", text="StarNum")
    treeview.heading("#6", text="ID")
    treeview.heading("#7", text="Title")

    # Insert the data into the treeview
    for row in data:
        treeview.insert("", "end", values=row)

    # Copy to Clipboard Button
    def copy_to_clipboard():
        clipboard_data = "%s\t %s\t %d results\n"%(urly, "", 3) #category, len(pieces))
        for row in data:
            clipboard_data += "\t".join(map(str, row)) + "\n"
        window.clipboard_clear()
        window.clipboard_append(clipboard_data)

    copy_button = Button(window, text="Copy to Clipboard", command=copy_to_clipboard, bg="gray", fg="white")
    copy_button.pack()



# Function to handle button click
def handle_scrape():
    url = url_entry.get()
    output_text.delete(1.0, "end")  # Clear previous output
    output_text.insert("end", "Scraping in progress...\n")
    output_text.update()
    data = scrape_site(url)
    display_results(data, url)
    output_text.insert("end", "Scraping completed. Results displayed.\n")
    output_text.update()

# Create the GUI window
window = Tk()
window.title("Web Scraper")
window.configure(bg="black")  # Set background color to black

# URL Label and Entry
url_label = Label(window, text="Enter the URL:", bg="black", fg="white")  # Set label colors
url_label.pack()
url_entry = Entry(window)
url_entry.pack()

# Scrape Button
scrape_button = Button(window, text="Scrape", command=handle_scrape, bg="gray", fg="white")  # Set button colors
scrape_button.pack()

# Output Text
output_text = Text(window, height=20, width=100, bg="black", fg="white")  # Set text widget colors
output_text.pack()

# Start the GUI event loop
window.mainloop()