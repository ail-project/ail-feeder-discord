#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import base64
import configparser
import gzip
import hashlib
import math
import os
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
import urlextract
import validators
from urlextract import URLExtract
from pyail import PyAIL


def stopProgram():
    if (args.verbose):
        print("The scanning time is up. Exiting now...")
    os._exit(0)


def getMessages(url, server):
    if url:
        result = client.searchMessages(guildID=server['id'], has="link").json()
    else:
        result = client.searchMessages(guildID=server['id'], textSearch=args.query).json()
    total_messages = result['total_results']
    messages = []

    if args.messagelimit > 25 and total_messages > 25:
        iterations = math.ceil(total_messages/25)
        for i in range(iterations):
            if url:
                msgs = client.searchMessages(guildID=server['id'], has="link", afterNumResults=i*25).json()
            else:
                msgs = client.searchMessages(guildID=server['id'], textSearch=args.query, afterNumResults=i*25).json()
            for msg in msgs['messages']:
                messages.append(msg[0])

    else:
        if url:
            msgs = client.searchMessages(guildID=server['id'], has="link").json()
        else:
            msgs = client.searchMessages(guildID=server['id'], textSearch=args.query).json()
        if "messages" in msgs:
            if args.messagelimit < total_messages:
                counter = 0
                for msg in msgs['messages']:
                    if counter < args.messagelimit:
                        messages.append(msg[0])
                        counter += 1
                    else:
                        break
            else:
                for msg in msgs['messages']:
                    messages.append(msg[0])
    
    return messages


def scanServer(server):
    # Search through the text messages for the query
    messages = getMessages(False, server)
    for message in messages:
        signal.alarm(10)
        try:
            createJson(message, server['id'], server['name'])
        except TimeoutError:
            print("Timeout reached for creating JSON of message: {}".format(message[0]['id']), file=sys.stderr)
            sys.exit(1)
        else:
            signal.alarm(0)

    # Search through the text messages for URLs
    messages = getMessages(True, server)
    for message in messages:
        extractURLs(message)


def createJson(message, server_id, server_name):
    # Caching
    if r.exists("c:{}".format(message['id'])):
        print("Message {} already processed".format(message['id']), file=sys.stderr)
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
        output_message['meta']['referenced-message']['guild-id'] = message['message_reference']['guild_id']
        output_message['meta']['referenced-message']['channel-id'] = message['message_reference']['channel_id']
        output_message['meta']['referenced-message']['message-id'] = message['message_reference']['message_id']
        output_message['meta']['referenced-message']['url'] = "https://discord.com/channels/" + message['message_reference']['guild_id'] + "/" + message['message_reference']['channel_id'] + "/" + message['message_reference']['message_id']

        if (args.replies):
            # Avoid being ratelimited
            time.sleep(1)
            referenced_message = client.getMessage(message['message_reference']['channel_id'], message['message_reference']['message_id']).json()
            if (args.verbose):
                print("Following the message thread...\n")
            createJson(referenced_message[0], server_id, server_name)

    output_message['data'] = message['content']
    #Encoding the content of the message into base64
    # m = hashlib.sha256()
    # m.update(message['content'].encode('utf-8'))
    # output_message['data-sha256'] = m.hexdigest()
    # output_message['data'] = base64.b64encode(gzip.compress(message['content'].encode()))

    if (args.verbose):
        print("Found a message which matches the query!")
        print("The JSON of the message is:")
    print(json.dumps(output_message, indent=4, sort_keys=True))

    # TODO: publish to AIL
    if args.verbose:
        print("Uploading the message to AIL...\n")
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
                if (args.verbose):
                    print("Found an invite link!")
                code = u.path.replace("/", "")
                joinServer(code)
                continue
            elif "discord.com" in u.hostname:
                continue

        # If the url is not valid, drop it and continue
        if not validators.url(surl):
            continue
        
        signal.alarm(10)
        try:
            article = newspaper.Article(surl)
        except TimeoutError:
            print("Timeout reached for {}".format(surl), file=sys.stderr)
            continue
        else:
            signal.alarm(0)

        # Caching
        if r.exists("cu:{}".format(base64.b64encode(surl.encode()))):
            print("URL {} already processed".format(surl), file=sys.stderr)
            if not args.nocache:
               continue
        else:
            r.set("cu:{}".format(base64.b64encode(surl.encode())), message['content'])
            r.expire("cu:{}".format(base64.b64encode(surl.encode())), cache_expire)
        
        if args.verbose:
            print("Downloading and parsing {}".format(surl))

        try:
            article.download()
            article.parse()
        except:
            if args.verbose:
                print("Unable to download/parse {}".format(surl), file=sys.stderr)
            continue

        output['data'] = article.html
        # Encoding the data of the URL into base64
        # m = hashlib.sha256()
        # m.update(article.html.encode('utf-8'))
        # output['data-sha256'] = m.hexdigest()
        # output['data'] = base64.b64encode(gzip.compress(article.html.encode()))
        nlpFailed = False

        try:
            article.nlp()
        except:
            if args.verbose:
                print("Unable to nlp {}".format(surl), file=sys.stderr)
            nlpFailed = True

            output['meta']['embedded-objects'] = []
            for embedded in message['embeds']:
                e = {}
                fields = ['title', 'type', 'url', 'description', 'timestamp', 'footer', 'image', 'thumbnail', 'video', 'provider', 'author', 'fields']
                for field in fields:
                    if field in embedded:
                        e[field] = embedded[field]
                output['meta']['embedded-objects'].append(e)

            if (args.verbose):
                print("Found a link!")
                print("The JSON of the extracted URL is:")
            print(json.dumps(output, indent=4, sort_keys=True))
            obj = json.dumps(output['data'], indent=4, sort_keys=True)
            
            if (len(obj) > args.maxsize):
                if (args.verbose):
                    print("The data from this URL is too big to upload! Consider increasing the maxsize if you still want it to be uploaded.")
                    print("Continuing with the next one...\n")
                continue

            # TODO: publish to AIL
            if args.verbose:
                print("Uploading the URL to AIL...\n")
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

        if (args.verbose):
            print("Found a link!")
            print("The JSON of the extracted URL is:")
        print(json.dumps(output, indent=4, sort_keys=True))
        obj = json.dumps(output['data'], indent=4, sort_keys=True)
        if (len(obj) > args.maxsize):
            if (args.verbose):
                print("The data from this URL is too big to upload! Consider increasing the maxsize if you still want it to be uploaded.")
                print("Continuing with the next one...\n")
            continue

        # TODO: publish to AIL
        if args.verbose:
            print("Uploading the URL to AIL...\n")
        data = output['data']
        metadata = output['meta']
        source = ailurlextract
        source_uuid = uuid
        pyail.feed_json_item(data, metadata, source, source_uuid)


def joinServer(code):
    server = client.getInfoFromInviteCode(code).json()['guild']
    if (args.verbose):
        print("Invite code: {}".format(code))
        print("Trying to join the server {} now...".format(server['name']))
    server_id = server['id']
    if not server_id in scanned_servers:
        # The waiting time can be reduced, but the lower the time waited between joining servers, the higher the risk to get banned
        client.joinGuild(code, wait=10)
        if (args.verbose):
            print("Joined the server successfully!")
            print("Scanning the newly joined server...")
        scanServer(server)
        if (args.verbose):
            print("Scan successful! Continuing the previous scan...\n")
    else:
        if (args.verbose):
            print("Already in this server! Continuing scan...\n")


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
    print("Ail section not found in the config file. Add it and the necessary fields and try again!", sys.stderr)
    sys.exit(0)
try:
    pyail = PyAIL(ail_url, ail_key, ssl=False)
except Exception as e:
    print(e)
    sys.exit(0)

# Argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("query", help="query to search on Discord to feed AIL")
parser.add_argument("--verbose", help="verbose output", action="store_true")
parser.add_argument("--nocache", help="disable cache", action="store_true")
parser.add_argument("--messagelimit", help="maximum number of messages to fetch", type=int, default=message_limit)
parser.add_argument("--replies", help="follow the messages of a thread", action="store_true")
parser.add_argument("--maxsize", help="the maximum size of a url in bytes", type=int, default=4194304) # 4MiB
parser.add_argument("--scantime", help="the amount of time the application should keep listening for new messages in seconds (turned off by default)", type=int, default=0) # 0 means turned off
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
        print("Logged in as {}#{}".format(user['username'], user['discriminator']))

        # Scan the servers the user is already on
        servers = client.getGuilds().json()
        if (args.verbose):
            print("Scanning the servers the user is on...\n")
        for server in servers:
            scanned_servers.append(server['id'])
            if (args.verbose):
                print("Scanning '{}' now...\n".format(server['name']))
            scanServer(server)
            if (args.verbose):
                print("Done scanning '{}'\n".format(server['name']))
        
        if (args.verbose):
            print("Done with the scan of existing servers!")
            print("Sleeping for 2 seconds to avoid rate limits...\n")
        time.sleep(2)
        
        # Once we scanned all the servers the user is already on, we join the ones from server-invite-codes.txt and search those as well
        if (args.verbose):
            print("Joining the servers from the server invite codes...\n")
        codes = open("etc/server-invite-codes.txt", "r")
        for code in codes:
            joinServer(code)
        if (args.verbose):
            print("Done joining and scanning the given servers!\n")

        if args.scantime == 0:
            print("All done! Exiting now...")
            os._exit(0)
        else:
            if (args.verbose):
                print("Listening for new incoming messages now!\n")
            # Set a timer for listening for new messages and stop execution once the time is up
            Timer(args.scantime, stopProgram).start()
    
    # Continuously check for new messages
    if resp.event.message:
        if (args.verbose):
            print("A new message came in!\n")
        m = resp.parsed.auto()
        # Check if the query is in the message, if it is, extract the data
        if re.search(args.query, m['content'], re.IGNORECASE):
            createJson(m, m['guild_id'], "")
        # Check if there is a URL in the message, if there is, extract the data
        extractURLs(m)

# Establish connection
client.gateway.run(auto_reconnect=True)