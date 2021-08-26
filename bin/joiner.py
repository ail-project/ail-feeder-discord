import logging
import time

from selenium import webdriver
from selenium.webdriver.firefox.options import Options


def start(verbose):
    logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s:%(message)s', level=logging.INFO, datefmt='%I:%M:%S')
    
    options = Options()
    options.headless = True
    browser = webdriver.Firefox(options=options)

    if verbose:
        logging.info("Joining servers...")
    codes = open("etc/server-invite-codes.txt").readlines()
    if len(codes) == 0:
        return False
    counter = 0
    for code in codes[::-1]:
        if counter >= 20:
            break
        browser.get("https://discord.com/invite/{}".format(code))
        del codes[-1]
        time.sleep(1)
        counter += 1
        if verbose:
            logging.info("Joined {} servers.".format(counter))

    if verbose:
        logging.info("Done joining servers! Accept the invite manually in the Discord app!\n")
    open('etc/server-invite-codes.txt', 'w').writelines(codes)

    browser.close()
    return True
