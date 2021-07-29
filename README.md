# ail-feeder-discord

External Discord feeder for AIL framework. (with a manually created user account)

> **Warning!** Automating user accounts is technically against TOS, so use at your own risk!

>It is recommended to use a fresh account for this, since the account might be banned/ phone locked!

## Install & Requirements

Install the Python dependencies:

```
pip3 install -U -r requirements.txt
```

This script will install the following Python libraries:
- [discum](https://github.com/Merubokkusu/Discord-S.C.U.M)
- [newspaper3k](https://github.com/codelucas/newspaper)
- [redis](https://github.com/andymccurdy/redis-py)
- [simplejson](https://github.com/simplejson/simplejson)
- [validators](https://github.com/kvesteri/validators)
- [pyail](https://github.com/ail-project/PyAIL)
- [urlextract](https://github.com/lipoja/URLExtract)

## How to use?

### Step 1

Create a file `token.txt` in the `etc/` folder. Add the Discord token of the account you want to use. 
[How to get the Discord user token](https://github.com/Tyrrrz/DiscordChatExporter/wiki/Obtaining-Token-and-Channel-IDs)

### Step 2

Create a file `server-invite-codes.txt` in the `etc/` folder if you want to automatically join and scan new servers. Add the invite codes in separate lines in this file (Make sure to not add the complete links! e.g., abcd1234 instead of https://discord.gg/abcd1234). This file can also be filled by running the `inviteRetriever.py` script. This script will populate the `server-invite-codes.txt` file with the codes from a Redis database, with credentials in the config file.

### Step 3

Replace the API key value in the config file with your API key value from AIL and make sure an instance of the ail-framework is running. You can also modify the other fields in the config file.

### Step 4

Join the desired servers. This can be done manually or automatically with some limits.
* For the manual version, just join the desired servers and proceed to step 5.
* For the automatic version, follow these steps:
    1. Open the Discord client and login or register. You should see the main menu of the Discord app. (Page with DMs etc)
    2. Run the `feeder.py` script and wait for the first scan to finish. Once the scan is finished, the program will give some options to continue. Choose 'join' to join 20 servers automatically.
    3. The program will attempt to join 20 servers of the `server-invite-codes.txt` file and open the prompts in the Discord app.
    4. **Wait for the program to finish** and then accept the invites to join the servers.
    5. Enter 'done' in the console, once you finished accepting the invites, to continue the scan.
    6. Repeat when the program gives the option to choose again.

### Step 5

Run the command below with the desired parameters and wait for execution to finish.

```
ail-feeder-discord/: python3 bin/feeder.py --help
usage: feeder.py [-h] [--verbose] [--nocache] [--replies] [--noleave] [--maxsize MAXSIZE] [--scantime SCANTIME]
                 [--messagelimit MESSAGELIMIT]
                 query

positional arguments:
  query                 query to search on Discord to feed AIL

optional arguments:
  -h, --help            show this help message and exit
  --verbose             verbose output
  --nocache             disable cache
  --replies             follow the messages of a thread
  --noleave             stay on the server after having scanned it
  --maxsize MAXSIZE     the maximum size of a url in bytes
  --scantime SCANTIME   the amount of time the application should keep listening for new messages in seconds (turned off by default)
  --messagelimit MESSAGELIMIT
                        maximum number of messages to fetch (multiples of 25) (-1 to get all)
```

## How does it work?

The program does the following in this order:

1. Login with the given account (token in `etc/token.txt`)
2. Fetch all the servers the user is already part of
3. Scan the channels in each server for the given query, if a match is found, extract the data and upload it to the AIL framework
4. After scanning for the query in the messages, the program looks for URLs in the channels, if a URL is found, extract the data and upload it to the AIL framework
5. When the scan is done, the program gives a few choices to continue:
    * 'exit' &rarr; finish the execution of the program
    * 'join' &rarr; join 20 servers from the `server-invite-codes.txt` file
    * 'leave' &rarr; leave all the servers the user is on
    * 'leave &#60;number&#62;' &rarr; leave &#60;number&#62; servers the user is on
6. Once 'exit' was passed as an option, the program starts to listen for incoming messages for `scantime` seconds
7. When a message comes in, matching the query or containing a link, the data is extracted and uploaded
8. When the `scantime` seconds are up, the program exits

NB: When a new message arrives during steps 2-5, the program treats the new message first and continues the previous scan after completing the new incoming message.

## Output to AIL

This feeder uses the PyAIL API to upload to the AIL framework.

The final result that is send to AIL is as follows:
- `source` is the name of the AIL feeder module
- `source-uuid` is the UUID of the feeder (unique per feeder)
- `data` is the base64 encoded value of the gziped data
- `data-sha256` is the SHA256 value of the uncompress data
- `meta` is the generic field where feeder can add the metadata collected