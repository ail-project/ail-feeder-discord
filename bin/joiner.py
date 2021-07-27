from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import time


options = Options()
options.headless = True
browser = webdriver.Firefox(options=options)

codes = open("etc/server-invite-codes.txt", "r")
counter = 0
for code in codes:
    if counter >= 20:
        break
    browser.get("https://discord.com/invite/{}".format(code))
    time.sleep(1)
    counter += 1
codes.close()

browser.close()