# Rating-Rover
A python script that gets Amazon's 100 best selling items from a category url you input. It then check the latest 250 reviews for each of those products to check if they've performed poorly recently. Listings that pass are written to csv file, along with their recent rating, ranking, price, titles, and low score.

There's also a more extensive version that scans the last 500 reviews instead.

The final file only scans one product for it's recent rating.

1. Install Requirements `pip3 install -r requirements.txt`
2. Run `python3 BesterScrapes.py`
3. Add Amazon BestSeller page URLS to program
4. Get data from [finals.csv](finals.csv)
