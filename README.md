# Li-Scraper

`LiScraper.py` is a single-pass script meant to extract a list of profiles from within your own LinkedIn network, according to the results of a search query e.g. `data scientist AND Singapore`. Within the script, the following parameters can be changed according to your requirements:

`pd.json`
Supply your LinkedIn credentials in this json with the following keys: `username` and `pd`.

`results.csv`
Profiles will be written to file in .csv format, one profile per row. You do not have to create this file before running the script.

`dataKey.json`
This will store the unique profile links that have been scraped. The scraper might halt for various reasons after execution, and this store helps to keep track of scraped profiles in case it needs to be restarted. You do not have to create this file before running the script.

`self.searchQuery`
This will contain the search query for profiles of interest. Note that LinkedIn will not allow viewing of profiles beyond 3rd degree connections. Also please be aware of biases arising from the [inspection paradox](https://towardsdatascience.com/the-inspection-paradox-is-everywhere-2ef1c2e9d709) when attempting to make inferences about the population using your social network.

`self.completedPages`
In case the scraper halts midway, this will enable you to pick up at the page where you left off.

`self.totalPages`
This determines the total number of pages that your scraper will evaluate. By default, LinkedIn does not display more than 100 pages of results for any search query.

