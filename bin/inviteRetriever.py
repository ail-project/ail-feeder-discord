import redis
import json
import re
import configparser


f = open("etc/server-invite-codes.txt", "w")
f.close()
config = configparser.ConfigParser()
config.read('etc/conf.cfg')
r = redis.Redis(host=config['db']['host'], port=config['db']['port'], password=config['db']['password'])

keys = r.keys('*')
for key in keys:
    value = json.loads(r.get(key).decode())
    inviteCode = value['inviteLink']
    c = open("etc/server-invite-codes.txt", "r")
    flag = False
    for line in c:
        if re.search(inviteCode, line):
            flag = True
    if not flag:
        f = open("etc/server-invite-codes.txt", "a")
        f.write(inviteCode + '\n')
        f.close()
    c.close()