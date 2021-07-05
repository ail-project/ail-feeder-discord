import discum
import json

t = open("src/token.txt", "r").read()
client = discum.Client(token=t, log={"console":False, "file":False})

@client.gateway.command
def helloworld(resp):
    if resp.event.ready_supplemental: #ready_supplemental is sent after ready
        user = client.gateway.session.user
        print("Logged in as {}#{}".format(user['username'], user['discriminator']))
        print("The user is in the following servers: ")
        servers = client.getGuilds().json()
        for i in servers:
            print(json.dumps(i, indent=4))

client.gateway.run(auto_reconnect=True)