import redis
import json
import configparser


f = open("etc/server-invite-codes.txt", "w")

config = configparser.ConfigParser()
config.read('etc/ail-feeder-discord.cfg')
r = redis.Redis(host=config['db']['host'], port=config['db']['port'], password=config['db']['password'])

keys = r.keys('*')
for key in keys:
    value = json.loads(r.get(key).decode())
    inviteCode = value['inviteLink']
    f.write(inviteCode + '\n')

f.close()