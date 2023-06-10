import tkinter as tk
from tkinter.ttk import Treeview
from ScrapeSite import scrape_site
import threading


class WebScraperGUI:
    def __init__(self, master):
        self.master = master
        master.title("Web Scraper")

        # Set up GUI elements
        self.configure_style()
        self.create_widgets()

    def configure_style(self):
        style = tk.ttk.Style()
        style.theme_use('clam')  # Use 'clam' theme for a consistent dark mode appearance
        style.configure('.', background='black', foreground='white')  # Set global background and foreground colors
        style.configure('TButton', padding=6)  # Increase padding for buttons
        style.map('TButton', background=[('active', 'gray')])  # Set button color on active state

    def create_widgets(self):
        # URL Label and Entry
        url_label = tk.Label(self.master, text="Enter the URL:")
        url_label.pack()
        self.url_entry = tk.Entry(self.master, width=100)
        self.url_entry.insert(0, "https://www.amazon.com/Best-Sellers-Pet-Supplies-Cat-Shampoos-Conditioners/zgbs/pet-supplies/2975274011/ref=zg_bs_nav_pet-supplies_3_3024148011")
        self.url_entry.pack()

        # Cutoff Integer Label and Entry
        int_label = tk.Label(self.master, text="Enter cutoff integer (30+ ideal):")
        int_label.pack()
        self.int_entry = tk.Entry(self.master, width=5)
        self.int_entry.pack()
        self.int_entry.insert(0, "30")

        # Scrape Button
        self.scrape_button = tk.Button(self.master, text="Scrape", command=self.handle_scrape)
        self.scrape_button.pack()

        # Output Text
        self.output_text = tk.Text(self.master, height=20, width=100, bg="black", fg="white")
        self.output_text.pack()

    def handle_scrape(self):
        url = self.url_entry.get()
        inty = int(self.int_entry.get())
        self.output_text.delete(1.0, tk.END)  # Clear previous output
        self.output_text.insert(tk.END, "Scraping in progress...\n")

        # Create a new thread for the scraping process
        scrape_thread = threading.Thread(target=self.scrape_and_display, args=(url, inty))
        scrape_thread.start()

    def scrape_and_display(self, url, inty):
        # Scrape the data
        data, cat = scrape_site(self.output_text, url, inty)

        # Update the GUI with the sorted data
        self.master.after(0, self.display_results, data, url, cat)
        self.master.after(0, self.output_text.insert, tk.END, "Scraping completed. Results displayed.\n")
        self.master.after(0, self.output_text.update)

    def display_results(self, data, urly, cat):
        # Create the Treeview widget
        treeview = Treeview(self.master, columns=("#0", "#1", "#2", "#3", "#4", "#5", "#6", "#7", "#8"), style='Treeview')
        treeview.pack()

        # Adjust column widths
        for i in range(9):
            treeview.column("#" + str(i), width=50 if i < 8 else 100)

        # Define the columns
        headings = ["Ranking", "Price", "100 Ave", "50 Ave", "Lowest", "TitStar", "StarNum", "Link", "Title"]
        for i, heading in enumerate(headings):
            treeview.heading("#" + str(i), text=heading)

        original_data = data
        reduced_data = None

        # Insert the data into the treeview
        def insert_data(data):
            for row in data:
                treeview.insert("", tk.END, values=row)

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
            self.master.clipboard_clear()
            self.master.clipboard_append(clipboard_data)

        insert_data(original_data)

        # Reduce Rows Button
        reduce_button = tk.Button(self.master, text="Show Best", command=reduce_rows, bg="gray", fg="white")
        reduce_button.pack()

        copy_button = tk.Button(self.master, text="Copy to Clipboard", command=copy_to_clipboard, bg="gray", fg="white")
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


if __name__ == "__main__":
    root = tk.Tk()
    WebScraperGUI(root)
    root.mainloop()
