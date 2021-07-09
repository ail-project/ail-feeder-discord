# ail-feeder-discord

External Discord feeder for AIL framework. (with a manually created user account)

> **Warning!** Automating user accounts is technically against TOS, so use at your own risk!

## Install & Requirements

- Install the Python dependencies:

```
pip3 install -U -r requirements.txt
```

This script will install the following Python libraries:
- [discum](https://github.com/Merubokkusu/Discord-S.C.U.M)
- [newspaper3k](https://github.com/codelucas/newspaper)
- [redis](https://github.com/andymccurdy/redis-py)
- [simplejson](https://github.com/simplejson/simplejson)
- [validators](https://github.com/kvesteri/validators)
- [urlextract](https://github.com/lipoja/URLExtract)
- [pyail](https://github.com/ail-project/PyAIL)

## How to use?

1. Create a file `token.txt` in the `etc/` folder in the root directory. Add the Discord token of the account you want to use. 
[How to get the Discord user token](https://github.com/Tyrrrz/DiscordChatExporter/wiki/Obtaining-Token-and-Channel-IDs)

2. Create a file `server-invite-codes.txt` in the `etc/` folder in the root directory if you want to automatically join and scan new servers. Add the invite codes in separate lines in this file. (Make sure to not add the complete links! e.g., abcd1234 instead of https://discord.gg/abcd1234)

3. Replace the API key value in the config file with your API key value from AIL. You can also modify the other fields in the config file.

4. Run the command below with the desired parameters and wait for execution to finish.

```
ail-feeder-discord/: python3 bin/feeder.py --help
usage: feeder.py [-h] [--verbose] [--nocache] [--messagelimit MESSAGELIMIT] [--replies] [--maxsize MAXSIZE] [--scantime SCANTIME] query

positional arguments:
  query                 query to search in the Discord server messages

optional arguments:
  -h, --help            show this help message and exit
  --verbose             verbose output
  --nocache             disable cache
  --replies             follow the messages of a thread
  --messagelimit MESSAGELIMIT
                        maximum number of messages to fetch
  --maxsize MAXSIZE     the maximum size of a url in bytes
  --scantime SCANTIME   the amount of time the application should keep listening for new messages in seconds (turned off by default)
```

## How does it work?

The program does the following in this order:

1. login with the given account (token in `etc/token.txt`)
2. fetch all the servers the user is already part of
3. scan the channels in each server for the given query, if a match is found, extract the data and upload it to the AIL framework
4. after scanning for the query in the messages, the program looks for URLs in the channels, if a URL is found, extract the data and upload it to the AIL framework
5. once all the servers, the user has been part of, are scanned, the program joins all the servers in `etc/server-invite-codes.txt` and repeats steps 3 and 4 for the newly joined servers
6. after this, the program starts to listen for incoming messages for `scantime` seconds
7. when a message comes in, matching the query or containing a link, the data is extracted and uploaded
8. when the `scantime` seconds are up, the program exits

NB: When a new message arrives during steps 2-5, the program treats the new message first and continues the previous scan after completing the new incoming message.

## Output to AIL

This feeder uses the PyAIL API to upload to the AIL framework.

The final result that is send to AIL is as follows:
- `source` is the name of the AIL feeder module
- `source-uuid` is the UUID of the feeder (unique per feeder)
- `data` is the base64 encoded value of the gziped data
- `data-sha256` is the SHA256 value of the uncompress data
- `meta` is the generic field where feeder can add the metadata collected