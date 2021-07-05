import discum
import json

t = open("src/token.txt", "r").read()
client = discum.Client(token=t, log={"console":False, "file":False})

@client.gateway.command
def start(resp):
    if resp.event.ready_supplemental: #ready_supplemental is sent after ready
        user = client.gateway.session.user
        print("Logged in as {}#{}".format(user['username'], user['discriminator']))
        scanServers(user)

def scanServers(user):
    print("The user is in the following servers: ")
    servers = client.getGuilds().json()
    print(json.dumps(servers, indent=4))
    for i in servers:
        print("The channels in server '" + i['name'] + "' are: ")
        # For now we only consider the text channels
        # All possible channel types: GUILD_TEXT, DM, GUILD_VOICE, GROUP_DM, GUILD_CATEGORY, GUILD_NEWS, GUILD_STORE, GUILD_NEWS_THREAD, GUILD_PUBLIC_THREAD, GUILD_PRIVATE_THREAD, GUILD_STAGE_VOICE
        channel_types = ['guild_text', 'dm', 'group_dm', 'guild_news', 'guild_store', 'guild_news_thread', 'guild_public_thread', 'guild_private_thread']
        channels = client.gateway.findVisibleChannels(i['id'], channel_types)
        print(json.dumps(channels, indent=4))
        for j in channels:
            print("The messages in channel " + j + " are: ")
            print(json.dumps(client.getMessages(j, 5).json(), indent=4))

def joinServer():
    code = input("Invitation code: ")
    print("Trying to join the server now...")
    client.joinGuild(code)
    print("Joined the server successfully!")

client.gateway.run(auto_reconnect=True)