import argparse
from time import sleep
import os
import csv
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import streamlit as st
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--csv", default = None, help = "Provide the CSV file path or Name")
args = parser.parse_args()

def write_csv(file_name, data_list):
    with open(file_name, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(data_list)

def read_csv(filename = 'keyword.csv'):
    keyword = []
    with open(filename, 'r') as f:
        for line in f.readlines():
            keyword.append(line)
    return keyword

class WebRank:
    def __init__(self, latitude = None, longitude = None):
        opts = webdriver.ChromeOptions()
        opts.accept_insecure_certs = True
        opts.ignore_certificate_errors = True
        lat = args.lat if latitude is None else latitude
        lon = args.long if longitude is None else longitude
        opts.add_argument(f"--use-fake-ui-for-media-stream=\"{lat},{lon}\"")
        opts.add_argument(f"--use-fake-device-for-media-stream")
        opts.add_argument("start-maximized")
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),options=opts)
        self.driver.implicitly_wait(15)
        if lat is not None and lon is not None:
            self.driver.execute_cdp_cmd("Emulation.setGeolocationOverride", {
                "latitude": lat,
                "longitude": lon,
                "accuracy": 100,
            })
        self.driver.get("https://www.google.com")
        geolocation_script = """
            navigator.geolocation.getCurrentPosition(function(position) {
                console.log("Latitude: " + position.coords.latitude);
                console.log("Longitude: " + position.coords.longitude);
            });
        """
        print(self.driver.execute_script(geolocation_script))

    def get_website_rank(self, keywords):
        pom = pageObjects(self.driver)
        for item in keywords:
            pom.search_content(item)
            try:
                pom.get_cite_name(item)
            except:
                pom.clear_input()
                write_csv('cite.csv', ["No Rank Found ", item])


class pageObjects:
    __SEARCH_BOX = (By.TAG_NAME, 'textarea')
    __MORE_RESULT = (By.XPATH, "//span[text()='More results']")
    __URL_PATTERN = '\bhttps?:\/\/(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'

    def __init__(self, driver):
        self.__driver = driver
        self.__wait = WebDriverWait(self.__driver, 15)

    def search_content(self, keyword):
        search = self.__driver.find_element(*pageObjects.__SEARCH_BOX)
        if search.is_displayed():
            search.send_keys(keyword, Keys.ENTER)
            sleep(3)

    def get_cite_name(self, keyword):
        rank = 1
        while True:
            __CITE_NAME_BY, __CITE_NAME_VALUE = (By.XPATH, f"(//cite)[{rank}]")
            cite = self.__driver.find_element(__CITE_NAME_BY, __CITE_NAME_VALUE)
            cite_length = len(self.__driver.find_elements(By.XPATH, "//cite"))
            print(cite_length, rank, keyword, cite.text)
            self.__driver.execute_script("arguments[0].scrollIntoView();", cite)
            try:
                self.__driver.find_element(*pageObjects.__MORE_RESULT).click()
            except:
                pass
            data_dic={}

            if cite.text.__contains__('codezeros'):
                # write_csv('cite.csv', [str(rank), ", ", cite.text, " ,- Keyword::: ", ", ", keyword])
                write_csv('cite.csv', [str(rank), keyword, cite.text])
                
                break
            rank += 1
        self.clear_input()

    def clear_input(self):
        self.__driver.find_element(*pageObjects.__SEARCH_BOX).clear()


location_coords = {
    "India":(23.020817937918395, 79.58166885899512),
    "USA": (37.0902, -95.7129),
    "Canada":(60.30483315220337, -110.25928084440059),
    "UK":(55.13417974025186, -3.131820054182296),
    "UAE":(23.820095638901083, 54.11981547291353),
    "Australia":(-24.890563592836173, 135.5169683142086)
    # Add more locations and their coordinates here
}

st.title('Web Rank Search')

location = st.selectbox('Select Location', options=list(location_coords.keys()))

# File uploader
uploaded_file = st.file_uploader("Choose a keyword's CSV file", type="csv")
if uploaded_file is not None:
    # Read the file using Pandas
    df = pd.read_csv(uploaded_file)
    keywords = df.iloc[:, 0].tolist()  # Assuming keywords are in the first column

    if st.button('Process'):
        # Instantiate and run WebRank
        lat, lon = location_coords.get(location, (None, None))

        web_rank = WebRank(latitude=lat, longitude=lon)
        web_rank.get_website_rank(keywords)

        # Provide download link for the output file
        with open('ranks.csv', 'rb') as file:
            st.download_button(label='Download Ranked file', data=file, file_name='cite.csv', mime='text/csv')

        st.success('Processing complete.')
