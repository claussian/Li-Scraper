# Li-Scraper

`LiScraper.py` is a single-pass script meant to extract a list of profiles from within your own LinkedIn network, according to the results of a search query e.g. `data scientist AND Singapore`. Please remember that [LinkedIn has a User Agreement that expressly prohibits crawlers and scraping activity on their website](https://www.linkedin.com/help/linkedin/answer/56347/prohibited-software-and-extensions?lang=en) - use this resource at your own risk.

Note that LinkedIn will not allow viewing of profiles beyond 3rd degree connections. **As such, please be aware of biases arising from the [inspection paradox](https://towardsdatascience.com/the-inspection-paradox-is-everywhere-2ef1c2e9d709) when attempting to make inferences about the population of Data Scientists or other professionals of interest using your own social network.**

Within the script, the following parameters can be changed according to your requirements:

`pd.json`
Supply your LinkedIn credentials in this json file with the following keys: `username` and `pd`.

`results.csv`
Profiles will be written to this file in .csv format, one profile per row. You do not have to create this file before running the script.

`dataKey.json`
This will store the unique profile links that have been scraped. The scraper might halt for various reasons after execution, and this store helps to keep track of scraped profiles in case it needs to be restarted. You do not have to create this file before running the script.

`self.searchQuery`
This will contain the search query for profiles of interest.

`self.completedPages`
In case the scraper halts midway, this will enable you to pick up at the page where you left off.

`self.totalPages`
This determines the total number of pages that your scraper will evaluate. By default, LinkedIn does not display more than 100 pages of results for any search query.

`self.expo`
This is a sample of 1000 waiting times in units of seconds, drawn from an exponential distribution with scale parameter 2 (i.e. mean of 1 click every 2 seconds). It is meant to simulate the distribution of gap times between human clicks in normal browser interactions. Change the scale parameter to simulate your preferred distribution of waiting times.


## Pipfile

A Pipfile is supplied with this package to install dependencies within a python virtual environment. In Terminal, `pipenv install` to install and `pipenv shell` to access the virtual environment.

## ChromeDriver
Li-Scraper uses ChromeDriver to emulate browser interactions, so make sure you have it installed. On a Mac, the easiest way is to use `brew cask install chromedriver` in Terminal. Otherwise, please refer to the ChromeDriver documentation: https://chromedriver.chromium.org/getting-started

## Execution
Once inside the virtual environment, run  `pipenv run python Li-Scraper.py`.

## Results
Results are written to the file `results.csv`, one profile per row. Because each profile may have multiple entries for education and
experience, the data for each of these parameters are written as a json object array, with the following structure:
### Experience
    {
        "data":[
            {
                "position": "Position 1",
                "company": "Company A",
                "duration": "X1 yrs Y1 mos"
            },
            {
                "position": "Position 2",
                "company": "Company B",
                "duration": "X2 yrs Y2 mos"
            }
        ]
    }
### Education
    {
        "data":[
            {
                "school": "School 1",
                "certification": "Bachelor's P1:::Domain Q1:::Merit R1"
            },
            {
                "school": "School 2",
                "certification": "Master's P2:::Domain Q2"
            }
        ]
    }
The field `certification` contains up to 3 sub-parameters: Certificate (Bachelors/Masters etc.), Domain (Biology/Computer Science etc.) and Merit (First Class Honours/ 4.0 GPA etc.). These sub-parameters are delimited by triple colon `:::`.

## Troubleshooting
The scraper works by emulating actual browser interactions, so often times it will fail if the browser has not updated to the correct state and does not contain the HTML elements being looked for. In particular, if the comment `Finding next icon...` is being repeated multiple times in Terminal, the driver is attempting to scroll down to the bottom of the page but the browser is not responding for some reason. In this situation, it suffices to manually scroll down the page to help the driver along. Otherwise, if the scraper crashes, it does not hurt to restart the execution. The file `dataKey.json` will ensure that the browser will pick up where it left off.

## Helper files
### keyset.json
This is a json file containing the XPath selectors mapping to the identity of the html tags containing the parameters of interest i.e. Name, Experience and Education. Considerable manual effort was invested into identifying these tags and their corresponding selectors. Do not be surprised if LinkedIn changes the identity of the html tags, in which case you will have to update the XPath selectors in this file manually.

