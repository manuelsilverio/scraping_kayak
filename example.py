"""
Created by Manuel Silverio

Example of Web scraper for Kayak flight info

You do not need to change the code.. just run it and it will find the flight info from Manchester to London
using the current date.

The info will be for the next day.

"""

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from bs4 import BeautifulSoup
import re
import pandas as pd
import numpy as np
from datetime import date, timedelta, datetime
import time


def scrape(origin, destination, startdate, days, requests=1):

    enddate = datetime.strptime(startdate, '%Y-%m-%d').date() + timedelta(days)
    enddate = enddate.strftime('%Y-%m-%d')

    url = "https://www.kayak.com/flights/" + origin + "-" + destination + "/" + startdate + "/" + enddate + "?sort=bestflight_a&fs=stops=0"
    print("\n" + url)

    chrome_options = webdriver.ChromeOptions()
    agents = ["Firefox/66.0.3", "Chrome/73.0.3683.68", "Edge/16.16299"]
    print("User agent: " + agents[(requests % len(agents))])
    chrome_options.add_argument('--user-agent=' + agents[(requests % len(agents))] + '"')
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome("chromedriver.exe", options=chrome_options,
                              desired_capabilities=chrome_options.to_capabilities())
    #driver.implicitly_wait(20)
    driver.get(url)

    # Check if Kayak thinks that we're a bot
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'lxml')

    if soup.find_all('p')[0].getText() == "Please confirm that you are a real KAYAK user.":
        print("Kayak thinks I'm a bot, which I am ... so let's wait a bit and try again")
        driver.close()
        time.sleep(20)
        return "failure"

    print('Waiting 20 seconds for website to load...')
    time.sleep(20)  # wait 20sec for the page to load

    print('Processing website')

    soup = BeautifulSoup(driver.page_source, 'lxml')

    # get the arrival and departure times
    deptimes = soup.find_all('span', attrs={'class': 'depart-time base-time'})
    arrtimes = soup.find_all('span', attrs={'class': 'arrival-time base-time'})
    meridies = soup.find_all('span', attrs={'class': 'time-meridiem meridiem'})

    deptime = []
    for div in deptimes:
        deptime.append(div.getText()[:-1])

    arrtime = []
    for div in arrtimes:
        arrtime.append(div.getText()[:-1])

    meridiem = []
    for div in meridies:
        meridiem.append(div.getText())

    deptime = np.asarray(deptime)
    deptime = deptime.reshape(int(len(deptime) / 2), 2)

    arrtime = np.asarray(arrtime)
    arrtime = arrtime.reshape(int(len(arrtime) / 2), 2)

    meridiem = np.asarray(meridiem)
    meridiem = meridiem.reshape(int(len(meridiem) / 4), 4)

    # Get the price
    #regex = re.compile('Common-Booking-MultiBookProvider (.*)multi-row Theme-featured-large(.*)')
    #price_list = soup.find_all('div', attrs={'class': regex})
    #price_list = soup.find_all('div', attrs={'class': 'Common-Booking-MultiBookProvider // multi-row // Theme-featured-large'})
    price_list = soup.select('div.Common-Booking-MultiBookProvider.Theme-featured-large.multi-row')

    price = []
    for div in price_list:
        val = div.getText().split('\n')[4][1:-1]
        price.append(int(val))

    df = pd.DataFrame({"origin": origin,
                       "destination": destination,
                       "startdate": startdate,
                       "enddate": enddate,
                       "price": price,
                       "currency": "USD",
                       "deptime_1": [m + str(n) for m, n in zip(deptime[:, 0], meridiem[:, 0])],
                       "arrtime_1": [m + str(n) for m, n in zip(arrtime[:, 0], meridiem[:, 1])],
                       "deptime_2": [m + str(n) for m, n in zip(deptime[:, 1], meridiem[:, 2])],
                       "arrtime_2": [m + str(n) for m, n in zip(arrtime[:, 1], meridiem[:, 3])]
                       })


    driver.close()  # close the browser

    return df


if __name__ == '__main__':
    #origin = input('Enter a valid Origin (for example MAN for Manchester): ').upper()
    #destination = input('Enter a Destination (for example LON for London): ').upper()

    from datetime import timedelta
    origin = 'MIL'
    destination = 'MAD'
    startdate = datetime.now() + timedelta(days=1)
    startdate = startdate.strftime("%Y-%m-%d")

    print('Scraping for origin: {} and destination: {}, for date: {}'.format(origin, destination, startdate))
    df = scrape(origin=origin, destination=destination, startdate=startdate, days=3)

    print('Flight data fetched. Now saving data frame in CSV file on the same directory this script is running.')
    df.to_csv('example_output.csv')
    print('Example finished')

