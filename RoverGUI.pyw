from tkinter import *
from tkinter.ttk import Treeview, Progressbar
from ScrapeSite import scrape_site
import threading


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

def remove_low_averages(data_list):
    reduced_list = []
    max_100 = 0
    max_50 = 0

    for row in data_list:
        curr_100 = row[2]
        curr_50 = row[3]
        passed = False

        if curr_100 >= max_100:
            passed = True
            max_100 = curr_100
            
        if curr_50 >= max_50:
            passed = True
            max_50 = curr_50
            
        if passed:
            reduced_list.append(row)

    return reduced_list

def scrape_and_display(url, inty):
    # Scrape the data
    data, cat = scrape_site(output_text, url, inty)

    # Update the GUI with the sorted data
    window.after(0, display_results, data, url, cat)
    window.after(0, output_text.insert, "end", "Scraping completed. Results displayed.\n")
    window.after(0, output_text.update)
    
        # Update progress bar
    progress_var.set(100)

# Function to handle button click
def handle_scrape():
    url = url_entry.get()
    inty = int(int_entry.get())
    output_text.delete(1.0, "end")  # Clear previous output
    output_text.insert("end", "Scraping in progress...\n")
    output_text.update()

    # Create a new thread for the scraping process
    progress_var = DoubleVar()
    progress_bar = Progressbar(window, variable=progress_var, maximum=100)
    progress_bar.pack()

    # Create a new thread for the scraping process
    scrape_thread = threading.Thread(target=scrape_and_display, args=(url,inty,))
    scrape_thread.start()
    
    # Update progress bar periodically
# Update progress bar periodically
    def update_progress():
        if scrape_thread.is_alive():
            progress = progress_var.get()  # Get the progress value from the variable
            progress_bar["value"] = progress  # Update the progress bar value
            window.after(100, update_progress)



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

# Scrape Button
scrape_button = Button(window, text="Scrape", command=handle_scrape, bg="white", fg="black")  # Set button colors
scrape_button.pack()

# Output Text
output_text = Text(window, height=20, width=100, bg="black", fg="white")  # Set text widget colors
output_text.pack()

# Start the GUI event loop
window.mainloop()