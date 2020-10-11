from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from parsel import Selector
from functools import reduce
from time import sleep
import numpy as np
import time
import ujson
import csv
import random
import os
import re

class Scraper:

    def __init__(self):

        self.credentials = 'pd.json'
        self.keyset = 'keyset.json'
        self.results = 'results.csv'
        self.profileKey = 'dataKey.json'
        self.searchQuery = 'data scientist AND Singapore'
        self.completedPages = 0
        self.totalPages = 100
        self.expo = list(np.random.exponential(2, 1000))

        print('\n')
        print('Reading in files...')

        with open(self.credentials) as f:
            self.pd = ujson.load(f)

        with open(self.keyset) as g:
            self.ks = ujson.load(g)
        
        dKExist = os.path.isfile(self.profileKey)
        if dKExist:
            with open(self.profileKey) as h:
                self.dataKey = ujson.load(h)
        else:
            self.dataKey = {}
            with open(self.profileKey, 'w') as d:
                ujson.dump(self.dataKey, d)

        resultsExist = os.path.isfile(self.results)
        if resultsExist:
            with open(self.results) as g:
                next(g)
                filereader = csv.reader(g)
                self.dataList = [line for line in filereader]
                print('%d existing rows in dataList.' %len(self.dataList))
        else:
            self.dataList = []
            with open(self.results, 'w') as w:
                writer = csv.writer(w)
                writer.writerows([['id','name','title','experience','education']])
                print('Writing new results list.')
        
        #exponential distribution sample of wait times with lambda of 1 in 2s
        # with open('exponential_lambda_1_in_2.csv') as b:
        #     next(b)
        #     self.expo = [float(line) for line in b]
        

        self.scrollCounter = 0
        self.profileCounter = {}
       
    def returnXPathOrClassName(self, current, key):
        array = self.ks[current]
        ident = list(filter(lambda x: x['key'] == key, array))
        value = ident[0]['value']
        if len(value.split(':::')) == 1:
            return value
        else:
            return value.split(':::')

    def getMultipleConditions(self, classArray):
        mcArray = list(map(lambda x: f" and contains(@class, '{x}')", classArray[1:]))
        firstElem = f"contains(@class, '{classArray[0]}')"
        mc = reduce((lambda x,y: x + y), [firstElem] + mcArray)
        return mc

    def getName(self, selector, driver):
        nameClassArray = self.returnXPathOrClassName('profile', 'name')
        try:
            nameClass = self.getMultipleConditions(nameClassArray)
            name = selector.xpath(f"//*[{nameClass}]/text()").get().strip()
        except:
            try:
                nameClass = self.returnXPathOrClassName('profile', 'name-alt')
                name = selector.xpath('//*[starts-with(@class, "'+ nameClass + '")]/text()').get().strip()
            except:
                sleep(2)
                print('finding name..')
                selector = Selector(text=driver.page_source) 
                return self.getName(selector, driver)
        return name

    def getTitle(self, selector, driver):
        titleClassArray = self.returnXPathOrClassName('profile', 'title')
        try:
            titleClass = self.getMultipleConditions(titleClassArray)
            title = selector.xpath(f"//*[{titleClass}]/text()").get().strip()
            #title = selector.xpath('//*[starts-with(@class, "'+ titleClass + '")]/text()').get().strip()
        except:
            sleep(1)
            print('finding title..')
            selector = Selector(text=driver.page_source) 
            return self.getTitle(selector, driver)
        return title

    def getLastSpan(self, h3):
        sel = Selector(text=h3)
        lastSpanXPath = self.returnXPathOrClassName('profile', 'last-span')
        sp = sel.xpath(lastSpanXPath).get()
        return sp

    def getTruncatedDuration(self, position):
        sel = Selector(text=position)
        durationClass = self.returnXPathOrClassName('profile', 'duration')
        dt = sel.xpath('//span[contains(@class,"' + durationClass + '")]/text()').getall()
        return dt

    def formatExperiences(self, position, experiences):
        sel = Selector(text=position)
        checkTitle = sel.xpath('//h3[1]/text()').get()
        if not checkTitle.strip(): # companies with more than 1 position
            hh = sel.xpath('//h3').getall()
            ls = list(map(lambda x: self.getLastSpan(x), hh))
            ld = self.getTruncatedDuration(position)
            assert(len(ls[1:]) == len(ld))

            for p,d in zip(ls[1:],ld):
                e = {"position": p, "company": ls[0], "duration": d}
                experiences['data'].append(e)
        else:
            p = checkTitle

            companyClass = self.returnXPathOrClassName('profile', 'company')
            c = sel.xpath('//*[contains(@class,"' + companyClass + '")]/text()').get()

            durationClass = self.returnXPathOrClassName('profile', 'duration')
            d = sel.xpath('//span[contains(@class,"' + durationClass + '")]/text()').get()
            e = {"position": p, "company": c, "duration": d}
            experiences['data'].append(e)
        
        return experiences

    def getExperiences(self, selector, driver):
        positPresent = False
        positionClass = self.returnXPathOrClassName('profile', 'position')
        while not positPresent:
            selector = Selector(text=driver.page_source)
            positions = selector.xpath('//*[contains(@class, "'+ positionClass + '")]').getall()
            try:
                positPresent = True
                assert(len(positions) >= 1)
            except:
                print('scrolling down to expose Experience selectors...')
                positPresent = False
                
                driver.execute_script("window.scrollTo(0, window.scrollY + 100)")
                self.scrollCounter += 1
                if self.scrollCounter > 20:
                    break
                else:
                    sleep(0.5)
        
        experiences = {"data": []}
        for p in positions:
            experiences = self.formatExperiences(p, experiences)
        return ujson.dumps(experiences)

    def getFullDegree(self, eduChunk, certBreakdownClass):
        sel = Selector(text=eduChunk)
        fullDegree = sel.xpath('//span[contains(@class,"' + certBreakdownClass + '")]/text()').getall()
        if len(fullDegree) == 1:
            return fullDegree[0]
        elif len(fullDegree) == 0:
            return ""
        else:
            fd = reduce((lambda x,y: x + ':::' + y), fullDegree)
            return fd

    def getEducation(self, selector, driver):
        eduPresent = False
        eduClass = self.returnXPathOrClassName('profile', 'education')
        while not eduPresent:
            selector = Selector(text=driver.page_source)
            schools = selector.xpath('//*[contains(@class, "'+ eduClass + '")]//h3[1]/text()').getall()
            try:
                eduPresent = True
                assert(len(schools) >= 1)           
            except:
                print('scrolling down to expose Education selectors...')
                eduPresent = False

                driver.execute_script("window.scrollTo(0, window.scrollY + 100)")
                self.scrollCounter += 1
                if self.scrollCounter > 20:
                    break
                else:
                    sleep(0.5)

        certClass = self.returnXPathOrClassName('profile', 'certification')
        certBreakdownClass = self.returnXPathOrClassName('profile', 'cert-breakdown')

        certifications = selector.xpath('//*[contains(@class, "'+ eduClass + '")]//div[contains(@class,"' + certClass + '")]').getall()
        certifications = list(map(lambda x: self.getFullDegree(x, certBreakdownClass), certifications))

        assert(len(schools) == len(certifications))

        educations = {"data": []}
        for s,c in zip(schools, certifications):
            e = {"school": s, "certification": c}
            educations['data'].append(e)
        return ujson.dumps(educations)

    def getData(self, selector, dataList, driver):
        dataRow = []
        
        dataRow.append(len(dataList)+1)

        name = self.getName(selector, driver)
        dataRow.append(name)

        title = self.getTitle(selector, driver)
        dataRow.append(title)

        experiences = self.getExperiences(selector, driver)   
        dataRow.append(experiences)

        education = self.getEducation(selector, driver)
        dataRow.append(education)

        dataList.append(dataRow)

        self.scrollCounter = 0

        return dataList

    def goToProfile(self, profileClassName, dataList, dataKey, driver):
        waitLength = random.choice(self.expo)
        results = driver.find_elements_by_class_name(profileClassName)
        totalLength = len(results)
        print('Total clickable: %d' %totalLength)

        for j,res in enumerate(results):
            href = results[j].get_attribute("href")
            checkInNetwork = re.findall("search", href) #LinkedIn member beyond 3rd degree
            if len(checkInNetwork) > 0:
                dataKey[href] = True
            if href not in dataKey:
                print('\n')
                print('Adding profile %d: %s' %(len(dataKey)+1, href))
                print('Waiting for %.2fs...' %waitLength)

                sleep(waitLength) # wait for a random amount of time before clicking

                results[j].click()

                sleep(3)

                selector = Selector(text=driver.page_source) 
                dataList = self.getData(selector, dataList, driver)
                dataKey[href] = True
                self.profileCounter[href] = True

                with open(self.results,'a') as r:
                    writer = csv.writer(r)
                    writer.writerows([dataList[-1]])
                
                with open(self.profileKey, 'w') as d:
                    ujson.dump(dataKey, d)
        
                print('...Done. Scraped %d profiles.' %len(dataList))
                print('Going back...')
                print('\n')

                driver.back()

                break
            else:
                self.profileCounter[href] = True
                if j+1 == len(results):
                    print('No new results in current view. Scrolling down for more results...')
                    driver.execute_script("window.scrollTo(0, window.scrollY  + 80)")
        
        sleep(0.5)

        if len(self.profileCounter) < 10:
            return self.goToProfile(profileClassName, dataList, dataKey, driver)   
        else:
            print('\n')
            print('Finished 10 profiles for current page.')
            self.profileCounter = {}
            return dataList, dataKey

    def run(self):
        start_time = time.time()

        print('\n')
        print('Starting driver...')
        driver = webdriver.Chrome('/usr/local/bin/chromedriver')

        driver.get('https://www.linkedin.com')

        current = 'first_set'

        print('\n')
        print('Finding username field...')
        try:
            username = driver.find_element_by_xpath(self.returnXPathOrClassName(current, 'username'))
            
        except:
            print('\n')
            print('Finding alternative username field...')
            current = 'second_set'
            signin_button = driver.find_element_by_xpath('/html/body/nav/a[3]')
            signin_button.click()

        username = driver.find_element_by_xpath(self.returnXPathOrClassName(current, 'username'))

        password = driver.find_element_by_xpath(self.returnXPathOrClassName(current, 'password'))
        
        print('\n')
        print('Providing credentials...')
        username.send_keys(self.pd['email'])

        password.send_keys(self.pd['pd'])

        login_button = driver.find_element_by_xpath(self.returnXPathOrClassName(current, 'login'))
        
        print('\n')
        print('Signing in.')
        login_button.click()

        sleep(1.5)

        print('\n')
        print('Finding search bar...')
        search_bar = driver.find_element_by_xpath(self.returnXPathOrClassName(current, 'search_bar'))

        search_bar.send_keys(self.searchQuery)

        print('\n')
        print('Entering search.')
        search_bar.send_keys(Keys.RETURN)

        sleep(3)

        print('\n')
        print('Finding people...')
        people = driver.find_element_by_xpath(self.returnXPathOrClassName(current, 'people'))

        people.click()

        sleep(1.5)

        print('\n')
        print('Search results.')
        # Returns list of 10 profiles
        #completedPages = int(len(self.dataList)/10)

        profileClassName = self.returnXPathOrClassName('profile', 'profile')

        for page in range(self.completedPages, self.totalPages+1):
            if page <= self.completedPages:
                continue
            else:
                if page == 1:
                    print('\n')
                    print('Page %d:' %page)
                else:
                    print('Scanning for right page...')             
                    pageXpath = self.returnXPathOrClassName(current, 'page-icon')
                    pageXpath = pageXpath.replace('ZZ', str(page))
                    while True:
                        try:
                            # scroll to bottom of page
                            driver.execute_script("document.body.scrollTop = document.body.scrollHeight;document.documentElement.scrollTop = document.documentElement.scrollHeight;window.scrollTo(0, document.documentElement.scrollTop || document.body.scrollTop);")
                            sleep(1)
                            pageIcon = driver.find_element_by_xpath(pageXpath)
                            break
                        except:
                            nextF = True
                            while nextF:
                                try:   
                                    nextXpath = self.returnXPathOrClassName(current, 'next-icon')
                                    nextIcon = driver.find_element_by_xpath(nextXpath)
                                    nextF = False
                                except:
                                    print('Finding next icon...')
                                    sleep(1)

                            nextIcon.click()
                            sleep(2)

                    print('\n')
                    print('Going to page %d:' %page)

                    pageIcon.click()

                    sleep(4)

                self.dataList, self.dataKey = self.goToProfile(profileClassName, self.dataList, self.dataKey, driver)

        end_time = time.time()
        elapsed = end_time - start_time
        print('\n')
        print('Time elapsed = %.2fmin' %(elapsed/60))

if __name__ == '__main__':
    Scraper().run()

    
    

    


