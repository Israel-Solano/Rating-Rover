# Rating-Rover

A python script that gets Amazon's 100 best selling items from a category url you input. It then check the latest 100 reviews for each of those products to check if they've performed poorly recently. Listings that pass are written to csv file, along with their recent rating, ranking, price, titles, and low score.

The final file only scans one product for it's recent rating.

1. Install Requirements `pip3 install -r requirements.txt`
2. Run `python3 Rover.py`
3. Add Amazon BestSeller page URLS to program, such as https://www.amazon.com/gp/bestsellers/electronics/7073956011
4. Get data from [finals.csv](finals.csv)

This web scrapper is legal as it only accesses public reviews: https://techcrunch.com/2022/04/18/web-scraping-legal-court/