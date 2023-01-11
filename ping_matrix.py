import requests

import argparse
import json
import os
from pprint import pprint
import time
import re

parser = argparse.ArgumentParser(description="monitoring plugin to ping a matrix bot")

parser.add_argument("--homeserver", required=True)
parser.add_argument("--message", required=True)
parser.add_argument("--response-pattern", default='^.*$')
parser.add_argument("--response-user", required=True)
parser.add_argument("--room", required=True)
parser.add_argument("--access-token", required=False)
parser.add_argument("--sync-timeout", default=60*1000, type=int)

args = parser.parse_args()

if not args.access_token:
    args.access_token = os.environ["ACCESS_TOKEN"]


session = requests.Session()
session.headers.update({"Authorization": "Bearer " + args.access_token, "Accept": "application/json"})

# Idea:
# 1. Sync to get a pagination token, filter so that we don't receive messages
# 2. Send our message
# 3. Sync to receive our answer


# 1. Sync
sync_filter = {
    "account_data": {"limit": 0},
    "presence": {"limit": 0},
    "room": {
        "account_data": {"limit": 0},
        "ephemeral": {"limit": 0},
        "rooms": [args.room],
        "state": {"limit":0},
        "timeline": {"limit":0},
    }
}
resp = session.get(args.homeserver + "/_matrix/client/v3/sync", params = {
    "timeout": 0,
    "filter": json.dumps(sync_filter)})
resp.raise_for_status()
next_batch = resp.json()["next_batch"]


# 2. Send message

send_url = args.homeserver +  "/_matrix/client/v3/rooms/{roomId}/send/m.room.message/{txnId}".format(roomId=args.room, txnId=str(time.time()))
send_event = {"body": args.message, "msgtype": "m.text"}
resp = session.put(send_url, headers={"Content-Type": "application/json"}, data=json.dumps(send_event))
resp.raise_for_status()

# 3. Sync to get anyswer
sync_filter["room"]["timeline"]["limit"] = 1
sync_filter["room"]["timeline"]["senders"] = [args.response_user]
sync_filter["room"]["timeline"]["types"] = ["m.room.message"]

due = time.time() + args.sync_timeout

while True:
    timeout = 
    resp = session.get(args.homeserver + "/_matrix/client/v3/sync", params = {
        "since": next_batch,
        "timeout": args.sync_timeout,
        "filter": json.dumps(sync_filter)})
    resp.raise_for_status()
    j = resp.json()
    pprint(j)
    if "rooms" in j:
        break
    next_batch = j["next_batch"]

event = j["rooms"]["join"][args.room]["timeline"]["events"][0]
body = event["content"]["body"]

ok = bool(re.search(args.response_pattern, body))
print(ok)
print(body)
exit(0 if ok else "Response did not match")
