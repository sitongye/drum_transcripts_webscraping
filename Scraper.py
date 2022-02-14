from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import time
import os
from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
from pathlib import Path
import json

# driver.get_cookies()
def get_and_save_sheet(selenium_cookie, song_page_url, main_output_folder):
    # main output folder should be absolute path
    # open a request session
    s = requests.Session()
    s.cookies.update({c["name"]: c["value"] for c in selenium_cookie})
    r = s.get(song_page_url)
    soup = BeautifulSoup(r.text, "html.parser")
    # get song title
    song_title = soup.find("h1", class_="text-black font-bold item-title heading").text
    artist,album,genre = [i.strip().replace("/","_") for i in soup.find("p", class_="text-grey-3 item-title body mt-1 mb-3").text.strip().replace("-", "").split("\n")]
    song_url = [i.split('resource_url":"')[-1].replace("\\","") for i in re.findall(str('\"resource_url\":\"https\:.*?\.pdf'), str(soup.find("content-lesson-action-buttons")))][0]
    song_dict = {"name": song_title, "artist": artist, "album": album, "genre": genre, "pdf_url": song_url}
    output_path = None
    if not artist:
        artist = "Unknown Artist"
        print("unknown artist: {}".format(song_url))
    if not album:
        album = "Unknown Album"
        print("unknown album: {}".format(song_url))

    if not os.path.exists(os.path.join(main_output_folder,artist)):
        os.makedirs(os.path.join(main_output_folder, artist))
    if not os.path.exists(os.path.join(main_output_folder, artist, album)):
        os.makedirs(os.path.join(main_output_folder, artist, album))
    pdf_response = requests.get(song_url)
    Path(os.path.join(main_output_folder, artist, album, "{}.pdf".format(song_title))).write_bytes(pdf_response.content)
    return song_dict

headers = requests.utils.default_headers()
headers.update({"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 13421.89.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36"})
driver = webdriver.Firefox(executable_path='./geckodriver')
driver.get('https://www.drumeo.com/members/lessons/songs')

WebDriverWait(driver,timeout=1000).until(lambda a: a.find_element_by_xpath('//*[@id="app"]/div[3]/div[4]/div/div[1]/h1'))
print("I am in")
last_height = driver.execute_script("return document.body.scrollHeight")
song_htmls = {}
while True:
    # scroll down to bottom
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    # add key down
    driver.find_element_by_tag_name("html").send_keys(Keys.PAGE_DOWN)
    time.sleep(10)
    new_height = driver.execute_script("return document.body.scrollHeight;")
    if new_height == last_height:
        break
    last_height = new_height
html =driver.page_source
song_soup = BeautifulSoup(html,"html.parser")
for tag in song_soup.find_all('div', attrs={"class": "flex flex-column"}):
    for song in tag.find_all("a"):
        if "subscribe" not in song["href"]:
            song_htmls[song["href"].split("/")[-1]] = song["href"]
print(song_htmls)
ck = driver.get_cookies()
for i in song_htmls.values():
    try:
        get_and_save_sheet(selenium_cookie=ck, song_page_url=i, main_output_folder="/home/sitongyewhiplash/PycharmProjects/web_scraping/drumeo_transcripts/outputs")
    except:
        print("error occurs at: ", i)
        continue

