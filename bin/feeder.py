import discum
import json
import hashlib
import base64
import time
import os
import argparse

t = open("etc/token.txt", "r").read()
client = discum.Client(token=t, log={"console":False, "file":False})

@client.gateway.command
def start(resp):
    if resp.event.ready_supplemental: #ready_supplemental is sent after ready
        user = client.gateway.session.user
        print("Logged in as {}#{}".format(user['username'], user['discriminator']))

        # Scan the servers the user is already on
        servers = client.getGuilds().json()
        for server in servers:
            print("Scanning the servers the user is on...")
            scanServer(server)
        print("Done with the scan of existing servers!")

        print("Sleeping for 5 seconds to avoid rate limits...")
        time.sleep(5)
        # Once we scanned all the servers the user is already on, we join the ones from server-invite-codes.txt and search those as well
        #joinServers()
        print("Done! Exiting now...")
        os._exit(0)

def scanServer(server):
    # All possible channel types: 
    # guild_text, dm, guild_voice, group_dm, guild_category, guild_news, guild_store, guild_news_thread, guild_public_thread, guild_private_thread, guild_stage_voice
    # For now we only consider the text channels
    channel_types = ['guild_text', 'dm', 'group_dm', 'guild_news', 'guild_store', 'guild_news_thread', 'guild_public_thread', 'guild_private_thread']
    channels = client.gateway.findVisibleChannels(server['id'], channel_types)
    
    for channel in channels:
        messages = client.getMessages(channel, 5).json()
        for message in messages:
            info = createJson(message, server, channel)
            print("The formatted metadata of the message is:")
            print(json.dumps(info, indent=4, sort_keys=True))

def createJson(message, server, channel):
    info = {}
    info['message:id'] = message['id']
    info['message:url'] = "https://discord.com/channels/" + server['id'] + "/" + channel + "/" + message['id']

    #Encoding the content of the message into base64
    content_bytes = message['content'].encode('utf-8')
    info['message:content-sha256'] = hashlib.sha256(content_bytes).hexdigest()
    info['message:content'] = base64.b64encode(content_bytes).decode('utf-8')
    #info['message:content'] = message['content']

    info['channel:id'] = message['channel_id']
    info['sender:id'] = message['author']['id']
    info['sender:profile'] = message['author']['username'] + "#" + message['author']['discriminator']
    info['server:id'] = server['id']
    info['server:name'] = server['name']

    info['attachments'] = []
    for attachment in message['attachments']:
        a = {}
        a['id'] = attachment['id']
        a['filename'] = attachment['filename']
        a['url'] = attachment['url']
        a['proxy_url'] = attachment['proxy_url']
        a['type'] = attachment['content_type']
        info['attachments'].append(a)

    info['usermentions'] = []
    for mention in message['mentions']:
        m = {}
        m['id'] = mention['id']
        m['sender:profile'] = mention['username'] + "#" + mention['discriminator']
        info['usermentions'].append(m)

    info['rolementions'] = []
    for rolemention in message['mention_roles']:
        rm = {}
        rm['role:id'] = rolemention
        info['rolementions'].append(rm)
    
    info['mentioneveryone'] = message['mention_everyone']

    info['reactions'] = []
    if 'reactions' in message:
        for reaction in message['reactions']:
            r = {}
            r['id'] = reaction['emoji']['id']
            r['name'] = reaction['emoji']['name']
            r['count'] = reaction['count']
            info['reactions'].append(r)

    info['timestamp'] = message['timestamp']
    info['edited_timestamp'] = message['edited_timestamp']
    info['webhook_id'] = ''
    if 'webhook_id' in message:
        info['webhook_id'] = message['webhook_id']

    info['embedded-objects'] = []
    for embedded in message['embeds']:
        e = {}
        # All the fields that exist: 
        # title, type, url, description, timestamp, color, footer, image, thumbnail, video, provider, author, fields
        fields = ['title', 'type', 'url', 'description']
        for field in fields:
            if field in embedded:
                e[field] = embedded[field]
        info['embedded-objects'].append(e)

    if 'message_reference' in message:
        info['referenced-message'] = {}
        info['referenced-message']['guild-id'] = message['message_reference']['guild_id']
        info['referenced-message']['channel-id'] = message['message_reference']['channel_id']
        info['referenced-message']['message-id'] = message['message_reference']['message_id']
        info['referenced-message']['url'] = "https://discord.com/channels/" + message['message_reference']['guild_id'] + "/" + message['message_reference']['channel_id'] + "/" + message['message_reference']['message_id']
        # TODO: Call the message analyser method recursively
    return info

def joinServers():
    codes = open("etc/server-invite-codes.txt", "r")
    for code in codes:
        print("Invite code: " + code)
        print("Trying to join the server now...")
        # The waiting time can be reduced, but the lower the time waited between joining servers, the higher the risk to get banned
        client.joinGuild(code, wait=10)
        print("Joined the server successfully!")
        print("Scanning the newly joined server...")
        server = client.getInfoFromInviteCode(code).json()['guild']
        scanServer(server)
        print("Scan successful")

client.gateway.run(auto_reconnect=True)