#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import base64
import configparser
import logging
import math
import os
import random
import re
import signal
import sys
import time
from threading import Timer
from urllib.parse import urlparse

import discum
import newspaper
import redis
import simplejson as json
import validators
from newspaper.article import ArticleException
from pyail import PyAIL
from urlextract import URLExtract

import joiner


def stopProgram():
    if args.verbose:
        logging.info("The scanning time is up. Exiting now...")
    os._exit(0)


def getMessages(url, server):
    time.sleep(round(random.uniform(5, 7), 2))

    if args.verbose:
        logging.info("Getting the amount of messages that match...")

    if url:
        result = client.searchMessages(guildID=server['id'], has="link").json()
    else:
        result = client.searchMessages(guildID=server['id'], textSearch=args.query).json()
    
    time.sleep(round(random.uniform(5, 7), 2))
    if 'message' in result and result['message'] == 'Missing Access': # {'message': 'Missing Access', 'code': 50001}
        if args.verbose:
            logging.error("Missing access, skipping...")
        return []
    if 'message' in result and result['message'] == 'Index not yet available. Try again later': # {'message': 'Index not yet available. Try again later', 'code': 110000, 'document_indexed': 0, 'retry_after': 2000}
        if args.verbose:
            logging.error("Server not yet indexed, try again later. Skipping...")
        return []

    total_messages = result['total_results']
    if args.verbose:
        logging.info("Found {} messages!".format(total_messages))
    messages = []
    if total_messages > 5000:
        total_messages = 5000 # 5000 messages is the maximum Discord can fetch {'code': 50035, 'errors': {'offset': {'_errors': [{'code': 'NUMBER_TYPE_MAX', 'message': 'int value should be less than or equal to 5000.'}]}}, 'message': 'Invalid Form Body'}
    if args.messagelimit == -1:
        args.messagelimit = total_messages

    if args.messagelimit > 25 and total_messages > 25:
        iterations = math.ceil(args.messagelimit/25)
        for i in range(iterations):
            logging.info("Getting messages {} to {}...".format(i*25+1, (i+1)*25))
            time.sleep(round(random.uniform(7, 10), 2))
            if url:
                msgs = client.searchMessages(guildID=server['id'], has="link", afterNumResults=i*25).json()
            else:
                msgs = client.searchMessages(guildID=server['id'], textSearch=args.query, afterNumResults=i*25).json()
            if "messages" in msgs:
                for msg in msgs['messages']:
                    messages.append(msg[0])
            else:
                if 'message' in msgs and msgs['message'] == 'Missing Access': # {'message': 'Missing Access', 'code': 50001}
                    if args.verbose:
                        logging.error("Missing access, skipping...")
                    return []
                else:
                    if args.verbose:
                        logging.info(msgs)
                        logging.error("Rate limited! Cancelling scan!")
                    os._exit(0)

    else:
        if url:
            msgs = client.searchMessages(guildID=server['id'], has="link").json()
        else:
            msgs = client.searchMessages(guildID=server['id'], textSearch=args.query).json()

        if "messages" in msgs:
            if args.messagelimit < total_messages:
                counter = 0
                for msg in msgs['messages']:
                    if counter <= args.messagelimit:
                        messages.append(msg[0])
                        counter += 1
                    else:
                        break
            else:
                for msg in msgs['messages']:
                    messages.append(msg[0])
        else:
            if 'message' in msgs and msgs['message'] == 'Missing Access': # {'message': 'Missing Access', 'code': 50001}
                if args.verbose:
                    logging.error("Missing access, skipping...")
                return []
            else:
                if args.verbose:
                    logging.info(msgs)
                    logging.error("Rate limited! Cancelling scan!")
                os._exit(0)

    
    if args.verbose:
        logging.info("Done scanning for messages!\n")
    return messages


def scanServer(server):
    # Search through the text messages for the query
    if args.verbose:
        logging.info("Scanning for the query in messages...")
    messages = getMessages(False, server)
    
    if args.verbose:
        logging.info("Looping through the found messages and extracting data...")
    
    for message in messages:
        signal.alarm(10)
        try:
            createJson(message, server['id'], server['name'])
        except TimeoutError:
            if args.verbose:
                logging.error("Timeout reached for creating JSON of message: {}".format(message[0]['id']))
            sys.exit(1)
        else:
            signal.alarm(0)

    if args.verbose:
        logging.info("Done looping through the found messages!\n")

    # Search through the text messages for URLs
    if args.verbose:
        logging.info("Scanning for URLs in messages...")
    messages = getMessages(True, server)
    if args.verbose:
        logging.info("Looping through the found messages and extracting data...")
    for message in messages:
        extractURLs(message)
    if args.verbose:
        logging.info("Done looping through the found messages!\n")


def createJson(message, server_id, server_name):
    # Caching
    if r.exists("c:{}".format(message['id'])):
        if args.verbose:
            logging.error("Message {} already processed".format(message['id']))
        if not args.nocache:
            return
    else:
        r.set("c:{}".format(message['id']), message['content'])
        r.expire("c:{}".format(message['id']), cache_expire)

    output_message = {}
    
    output_message['source'] = ailfeedertype
    output_message['source-uuid'] = uuid
    output_message['default-encoding'] = 'UTF-8'
    
    output_message['meta'] = {}
    output_message['meta']['message:id'] = message['id']
    output_message['meta']['message:url'] = "https://discord.com/channels/" + server_id + "/" + message['channel_id'] + "/" + message['id']

    output_message['meta']['channel:id'] = message['channel_id']
    output_message['meta']['sender:id'] = message['author']['id']
    output_message['meta']['sender:profile'] = message['author']['username'] + "#" + message['author']['discriminator']
    output_message['meta']['server:id'] = server_id
    output_message['meta']['server:name'] = server_name

    output_message['meta']['attachments'] = []
    for attachment in message['attachments']:
        a = {}
        a['id'] = attachment['id']
        a['filename'] = attachment['filename']
        a['url'] = attachment['url']
        a['proxy_url'] = attachment['proxy_url']
        a['type'] = attachment['content_type']
        output_message['meta']['attachments'].append(a)

    output_message['meta']['mentions:user'] = []
    for mention in message['mentions']:
        m = {}
        m['id'] = mention['id']
        m['sender:profile'] = mention['username'] + "#" + mention['discriminator']
        output_message['meta']['mentions:user'].append(m)

    output_message['meta']['mentions:role'] = []
    for rolemention in message['mention_roles']:
        rm = {}
        rm['role:id'] = rolemention
        output_message['meta']['mentions:role'].append(rm)
    
    output_message['meta']['mentions:everyone'] = message['mention_everyone']

    output_message['meta']['reactions'] = []
    if 'reactions' in message:
        for reaction in message['reactions']:
            react = {}
            react['id'] = reaction['emoji']['id']
            react['name'] = reaction['emoji']['name']
            react['count'] = reaction['count']
            output_message['meta']['reactions'].append(react)

    output_message['meta']['timestamp'] = message['timestamp']
    output_message['meta']['edited_timestamp'] = message['edited_timestamp']
    output_message['meta']['webhook:id'] = ''
    if 'webhook_id' in message:
        output_message['meta']['webhook_id'] = message['webhook_id']

    output_message['meta']['embedded-objects'] = []
    for embedded in message['embeds']:
        e = {}
        # All the fields that exist: 
        # title, type, url, description, timestamp, color, footer, image, thumbnail, video, provider, author, fields
        fields = ['title', 'type', 'url', 'description']
        for field in fields:
            if field in embedded:
                e[field] = embedded[field]
        output_message['meta']['embedded-objects'].append(e)

    if 'message_reference' in message:
        output_message['meta']['referenced-message'] = {}
        if 'guild_id' in message['message_reference']:
            output_message['meta']['referenced-message']['guild-id'] = message['message_reference']['guild_id']
        else:
            output_message['meta']['referenced-message']['guild-id'] = ''
        output_message['meta']['referenced-message']['channel-id'] = message['message_reference']['channel_id']
        output_message['meta']['referenced-message']['message-id'] = message['message_reference']['message_id']

        if args.replies:
            if args.verbose:
                logging.info("Getting the referenced-message and extracting it's data...")
            # Avoid being ratelimited
            time.sleep(round(random.uniform(5, 7), 2))
            referenced_message = client.getMessage(message['message_reference']['channel_id'], message['message_reference']['message_id']).json()
            if args.verbose:
                logging.info("Following the message thread...\n")
            createJson(referenced_message[0], server_id, server_name)

    output_message['data'] = message['content']

    if args.verbose:
        logging.info("Found a message which matches the query!")
        logging.info("Uploading the message to AIL...\n")

    data = output_message['data']
    metadata = output_message['meta']
    source = ailfeedertype
    source_uuid = uuid

    pyail.feed_json_item(data, metadata, source, source_uuid)


def extractURLs(message):
    extractor = URLExtract()
    urls = extractor.find_urls(message['content'])
    for url in urls:
        output = {}
        output['source'] = ailurlextract
        output['source-uuid'] = uuid
        output['default-encoding'] = 'UTF-8'

        output['meta'] = {}
        output['meta']['parent:discord:message_id'] = message['id']

        surl = url.split()[0]
        output['meta']['discord:url-extracted'] = surl
        u = urlparse(surl)

        if u.hostname is not None:
            if "discord.gg" in u.hostname:
                if args.verbose:
                    logging.info("Found an invite link!")
                code = u.path.replace("/", "")
                c = open('server-invite-codes.txt', 'a')
                c.write(code + '\n')
                c.close()
                # joinServer(code)
                continue
            elif "discord.com" in u.hostname:
                if "invite" in u.path:
                    code = u.path.split("/")[-1]
                    # joinServer(code)
                    c = open('server-invite-codes.txt', 'a')
                    c.write(code + '\n')
                    c.close()
                    continue
                else:
                    continue

        # If the url is not valid, drop it and continue
        if not validators.url(surl):
            continue
        
        signal.alarm(10)
        try:
            article = newspaper.Article(surl)
        except TimeoutError:
            if args.verbose:
                logging.error("Timeout reached for {}".format(surl))
            continue
        else:
            signal.alarm(0)

        # Caching
        if r.exists("cu:{}".format(base64.b64encode(surl.encode()))):
            if args.verbose:
                logging.error("URL {} already processed".format(surl))
            if not args.nocache:
               continue
        else:
            r.set("cu:{}".format(base64.b64encode(surl.encode())), message['content'])
            r.expire("cu:{}".format(base64.b64encode(surl.encode())), cache_expire)
        
        if args.verbose:
            logging.info("Downloading and parsing {}".format(surl))

        try:
            article.download()
            article.parse()
        except ArticleException:
            if args.verbose:
                logging.error("Unable to download/parse {}".format(surl))
            continue

        output['data'] = article.html

        nlpFailed = False

        try:
            article.nlp()
        except:
            if args.verbose:
                logging.error("Unable to nlp {}".format(surl))
            nlpFailed = True

            output['meta']['embedded-objects'] = []
            for embedded in message['embeds']:
                e = {}
                fields = ['title', 'type', 'url', 'description', 'timestamp', 'footer', 'image', 'thumbnail', 'video', 'provider', 'author', 'fields']
                for field in fields:
                    if field in embedded:
                        e[field] = embedded[field]
                output['meta']['embedded-objects'].append(e)

            if args.verbose:
                logging.info("Found a link!")
            obj = json.dumps(output['data'], indent=4, sort_keys=True)
            
            if len(obj) > args.maxsize:
                if args.verbose:
                    logging.error("The data from this URL is too big to upload! Consider increasing the maxsize if you still want it to be uploaded.")
                    logging.info("Continuing with the next one...\n")
                continue

            if args.verbose:
                logging.info("Uploading the URL to AIL...\n")
            data = output['data']
            metadata = output['meta']
            source = ailurlextract
            source_uuid = uuid
            pyail.feed_json_item(data, metadata, source, source_uuid)
            continue
    
        if nlpFailed:
            continue
        
        output['meta']['newspaper:text'] = article.text
        output['meta']['newspaper:authors'] = article.authors
        output['meta']['newspaper:keywords'] = article.keywords
        output['meta']['newspaper:publish_date'] = article.publish_date
        output['meta']['newspaper:top_image'] = article.top_image
        output['meta']['newspaper:movies'] = article.movies

        if args.verbose:
            logging.info("Found a link!")
        obj = json.dumps(output['data'], indent=4, sort_keys=True)
        if len(obj) > args.maxsize:
            if args.verbose:
                logging.error("The data from this URL is too big to upload! Consider increasing the maxsize if you still want it to be uploaded.")
                logging.info("Continuing with the next one...\n")
            continue

        if args.verbose:
            logging.info("Uploading the URL to AIL...\n")
        data = output['data']
        metadata = output['meta']
        source = ailurlextract
        source_uuid = uuid
        pyail.feed_json_item(data, metadata, source, source_uuid)


def joinServers():
    if not joiner.start(args.verbose):
        if args.verbose:
            logging.info("No more servers to join, exiting...")
        return False
    else:
        done = input("Type 'done', when you joined all the servers manually via the prompts.\n")
        while done != "done":
            done = input("Type 'done', when you joined all the servers manually via the prompts.\n")
        return True


def leaveServers(amount=-1):
    servers = client.getGuilds().json()
    time.sleep(round(random.uniform(5, 7), 2))
    if args.verbose:
        logging.info("Leaving the servers now...")
    if amount == -1:
        for server in servers:
            if args.verbose:
                logging.info("Leaving the server now...")
            client.leaveGuild(server['id'])
            time.sleep(round(random.uniform(7, 10), 2))
            if args.verbose:
                logging.info("Left the server!\n")
    elif amount >= 0:
        counter = 0
        for server in servers:
            if counter >= amount:
                break
            if args.verbose:
                logging.info("Leaving the server now...")
            client.leaveGuild(server['id'])
            time.sleep(round(random.uniform(7, 10), 2))
            if args.verbose:
                logging.info("Left the server!\n")
            counter += 1
    else:
        if args.verbose:
            logging.error("Invalid number given.\n")
    if args.verbose:
        logging.info("Left all the servers!\n")


def startScan():
    # Scan the servers the user is already on
    if args.verbose:
        logging.info("Scanning the servers the user is on...\n")
    servers = client.getGuilds().json()
    time.sleep(round(random.uniform(5, 7), 2))
    for server in servers:
        scanned_servers.append(server['id'])
        if args.verbose:
            logging.info("Scanning '{}' now...\n".format(server['name']))
        scanServer(server)
        if args.verbose:
            logging.info("Done scanning '{}'\n".format(server['name']))

        # Leaving the server with some wait time before
        if not args.noleave:
            if args.verbose:
                logging.info("Leaving the server now...")
            time.sleep(round(random.uniform(7, 10), 2))
            client.leaveGuild(server['id'])
            if args.verbose:
                logging.info("Left the server!\n")
    
    if args.verbose:
        logging.info("Done with the scan of existing servers!")
    time.sleep(round(random.uniform(5, 7), 2))


logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s:%(message)s', level=logging.INFO, datefmt='%I:%M:%S')

# Information about the feeder
uuid = "48093b86-8ce5-415b-ac7d-8add427ec49c"
ailfeedertype = "ail_feeder_discord"
ailurlextract = "ail_feeder_urlextract"

# Config reader
config = configparser.ConfigParser()
config.read('etc/ail-feeder-discord.cfg')

if 'general' in config:
    uuid = config['general']['uuid']
    message_limit = config['general']['message_limit']
else:
    message_limit = 50

if 'redis' in config:
    r = redis.Redis(host=config['redis']['host'], port=config['redis']['port'], db=config['redis']['db'])
else:
    r = redis.Redis()

if 'cache' in config:
    cache_expire = config['cache']['expire']
else:
    cache_expire = 86400

if 'ail' in config:
    ail_url = config['ail']['url']
    ail_key = config['ail']['apikey']
else:
    logging.error("Ail section not found in the config file. Add it and the necessary fields and try again!")
    sys.exit(0)
try:
    pyail = PyAIL(ail_url, ail_key, ssl=False)
except Exception as e:
    logging.error(e)
    sys.exit(0)

# Argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("query", help="query to search on Discord to feed AIL")
parser.add_argument("--verbose", help="verbose output", action="store_true")
parser.add_argument("--nocache", help="disable cache", action="store_true")
parser.add_argument("--replies", help="follow the messages of a thread", action="store_true")
parser.add_argument("--noleave", help="stay on the server after having scanned it", action="store_true")
parser.add_argument("--maxsize", help="the maximum size of a url in bytes", type=int, default=4194304) # 4MiB
parser.add_argument("--scantime", help="the amount of time the application should keep listening for new messages in seconds (turned off by default)", type=int, default=0) # 0 means turned off
parser.add_argument("--messagelimit", help="maximum number of messages to fetch (multiples of 25) (-1 to get all)", type=int, default=message_limit)
args = parser.parse_args()

# Initiate empty array to store scanned servers
scanned_servers = []

# Login and setup discum
t = open("etc/token.txt", "r").read()
client = discum.Client(token=t, log={"console":False, "file":False})

# Start of the scan
@client.gateway.command
def start(resp):
    # As soon as there is a response with the user being ready, the execution starts
    if resp.event.ready_supplemental:
        user = client.gateway.session.user
        if args.verbose:
            logging.info("Logged in as {}#{}".format(user['username'], user['discriminator']))

        # Scan the servers the user is already on
        startScan()
        choice = input("Type 'join' to join 20 servers of the server-invite-codes.txt.\nType 'leave' to leave all of the servers the user is currently on.\nType 'leave <number>' to leave a certain amount of servers.\nType 'exit' to finish the scan.\n")
        while choice != "exit":
            if choice == "join":
                # Check if the file is empty, if it is, return immediately
                if not joinServers():
                    break
                startScan()
            elif choice == "leave":
                leaveServers()
                pass
            elif re.search("leave (\d)+", choice):
                leaveServers(int(choice.split(" ")[-1]))
                pass
            else:
                if args.verbose:
                    logging.info("Please type either 'join', 'leave' 'leave <number>' or 'exit'!")
            choice = input("Type 'join' to join 20 servers of the server-invite-codes.txt.\nType 'leave' to leave all of the servers the user is currently on.\nType 'leave <number>' to leave a certain amount of servers.\nType 'exit' to finish the scan.\n")

        if args.scantime == 0:
            if args.verbose:
                logging.info("All done! Exiting now...")
            os._exit(0)
        else:
            if args.verbose:
                logging.info("Listening for new incoming messages now!\n")
            # Set a timer for listening for new messages and stop execution once the time is up
            Timer(args.scantime, stopProgram).start()
    
    # Continuously check for new messages
    if resp.event.message:
        if args.verbose:
            logging.info("A new message came in!\n")
        m = resp.parsed.auto()
        # Check if the query is in the message, if it is, extract the data
        if re.search(args.query, m['content'], re.IGNORECASE):
            createJson(m, m['guild_id'], "")
        # Check if there is a URL in the message, if there is, extract the data
        extractURLs(m)

# Establish connection
client.gateway.run(auto_reconnect=True)
