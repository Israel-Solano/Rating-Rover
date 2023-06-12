from time import sleep
import os
import re
import threading

from tkinter import *
from tkinter.ttk import Treeview

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

def remove_low_averages(data_list):
    reduced_list = []
    max_100 = 0
    max_50 = 0

    for row in data_list:
        curr_100 = (2.0 ** ((float(row[2]) - 4.0) * 10.0)) * row[6]
        curr_50 = (2.0 ** ((float(row[3]) - 4.0) * 10.0)) * row[6]
        passed = False

        if curr_100 > max_100:
            passed = True
            max_100 = curr_100
            
        if curr_50 > max_50:
            passed = True
            max_50 = curr_50
            
        if passed:
            reduced_list.append(row)

    return reduced_list

class ProgressBar:
    def __init__(self, total):
        self.progress = 0
        self.total = total

    def update_progress(self):
        self.progress += 1
        percent = int((self.progress / self.total) * 100)
        progress_str = "[{}{}] {}%".format("=" * (percent // 2), " " * ((100 - percent) // 2), percent)
        progress_label.config(text=progress_str)
        window.update_idletasks()

def move(driver):
    i = 0
    sleep(5)
    while i < 6:
        el = driver.find_element(By.CLASS_NAME, "a-pagination")
        action = ActionChains(driver)
        action.move_to_element(el)
        action.perform()
        sleep(0.25)
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
        progress_bar = ProgressBar(total_urls)
        
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
            progress_bar.update_progress()
    # Sort the data by "Starnum" in descending order
    return sorted(data_list, key=lambda x: (x[6]), reverse=True), category


def display_results(data, urly, cat):
    # Create the Treeview widget
    treeview = Treeview(window)
    treeview["columns"] = ("#0", "#1", "#2", "#3", "#4", "#5", "#6", "#7", "#8")
    treeview.pack()

    # Adjust column widths
    treeview.column("#0", width=50)  # Adjust the width of column 0
    treeview.column("#1", width=50)  # Adjust the width of column 1
    treeview.column("#2", width=50)  # Adjust the width of column 2
    treeview.column("#3", width=50)  # Adjust the width of column 3
    treeview.column("#4", width=50)  # Adjust the width of column 4
    treeview.column("#5", width=50)  # Adjust the width of column 5
    treeview.column("#6", width=50)  # Adjust the width of column 5
    treeview.column("#7", width=50)  # Adjust the width of column 6 
    treeview.column("#8", width=100) # Adjust the width of column 
    
    # Define the columns
    treeview.heading("#0", text="Ranking")
    treeview.heading("#1", text="Price")
    treeview.heading("#2", text="100 Ave")
    treeview.heading("#3", text="50 Ave")
    treeview.heading("#4", text="Lowest")
    treeview.heading("#5", text="TitStar")
    treeview.heading("#6", text="StarNum")
    treeview.heading("#7", text="Link")
    treeview.heading("#8", text="Title")

    original_data = data
    reduced_data = None

    # Insert the data into the treeview
    def insert_data(data):
        for row in data:
            treeview.insert("", "end", values=row)

    # Function to reduce rows
    def reduce_rows():
        nonlocal reduced_data, original_data

        if reduce_button.cget("text") == "Show Best":
            reduced_data = remove_low_averages(original_data)
            treeview.delete(*treeview.get_children())  # Clear existing rows
            insert_data(reduced_data)
            reduce_button.config(text="Show Original")
        else:
            treeview.delete(*treeview.get_children())  # Clear existing rows
            insert_data(original_data)
            reduce_button.config(text="Show Best")

    # Copy to Clipboard Button
    def copy_to_clipboard():
        clipboard_data = "%s\t %s\t %d results\n" % (cat, urly, len(data))
        if reduce_button.cget("text") == "Show Original" and reduced_data is not None:
            for row in reduced_data:
                clipboard_data += "\t".join(map(str, row)) + "\n"
        else:
            for row in original_data:
                clipboard_data += "\t".join(map(str, row)) + "\n"
        window.clipboard_clear()
        window.clipboard_append(clipboard_data)

    insert_data(original_data)
    # Reduce Rows Button
    reduce_button = Button(window, text="Show Best", command=reduce_rows, bg="gray", fg="white")
    reduce_button.pack()

    copy_button = Button(window, text="Copy to Clipboard", command=lambda: copy_to_clipboard(), bg="gray", fg="white")
    copy_button.pack()


def scrape_and_display(url, inty):
    # Scrape the data
    data, cat = scrape_site(output_text, url, inty)

    # Update the GUI with the sorted data
    window.after(0, display_results, data, url, cat)
    window.after(0, output_text.insert, "end", "Scraping completed. Results displayed.\n")
    window.after(0, output_text.update)

# Function to handle button click
def handle_scrape():
    url = url_entry.get()
    inty = int(int_entry.get())
    output_text.delete(1.0, "end")  # Clear previous output
    output_text.insert("end", "Scraping in progress...\n")
    output_text.update()

    # Create a new thread for the scraping process
    scrape_thread = threading.Thread(target=scrape_and_display, args=(url,inty,))
    scrape_thread.start()

# Create the GUI window
window = Tk()
window.title("Web Scraper")
window.configure(bg="black")  # Set background color to black

# URL Label and Entry
url_label = Label(window, text="Enter the URL:", bg="black", fg="white")  # Set label colors
url_label.pack()
url_entry = Entry(window, width = 100)
url_entry.insert(0, "https://www.amazon.com/Best-Sellers-Pet-Supplies-Cat-Shampoos-Conditioners/zgbs/pet-supplies/2975274011/ref=zg_bs_nav_pet-supplies_3_3024148011")
url_entry.pack()

# Val Label and Entry
int_label = Label(window, text="Enter cutoff integer(30+ ideal):", bg="black", fg="white")  # Set label colors
int_label.pack()
int_entry = Entry(window, width = 5)
int_entry.pack()
int_entry.insert(0, "30")

progress_label = Label(window, text="", font=("Arial", 12), pady=10)
progress_label.pack()

# Scrape Button
scrape_button = Button(window, text="Scrape", command=handle_scrape, bg="white", fg="black")  # Set button colors
scrape_button.pack()

# Output Text
output_text = Text(window, height=20, width=100, bg="black", fg="white")  # Set text widget colors
output_text.pack()

# Start the GUI event loop
window.mainloop()