
import queue
import sys
import threading
from time import sleep
from flask import Flask, request, Response
import json
import const
import requests
import os
import logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)
app = Flask(__name__)

# ------------------- Coordinator -------------------

# Permission can be given just to the next in the queue
wait_queue = queue.Queue()
blocked = False


@app.route("/get_permission", methods=['POST'])
def get_permission():
    global permission_queue
    global blocked
    print(f"blocked: {blocked}")
    print(f"Queue: {wait_queue.queue}")
    user = request.json['user']
    print(f"User {user} is requesting permission")
    if blocked:
        wait_queue.put(user)
    else:
        blocked = True
        print("blocked now")
        requests.post(get_user(user) + "/give_permission", json={"permission": True})
    return {}
 

@app.route("/release_permission", methods=['POST'])
def release_permission_coordinator():
    global permission_queue
    global blocked
    blocked = False
    if not wait_queue.empty():
        user = wait_queue.get()
        blocked = True
        requests.post(f"{get_user(user)}/give_permission", json={"permission": True})
    return {}

# ------------------- -------------------

# ------------------- Client -------------------
permission = False
coordinator = False
coordnator_name = "Coordinator"

@app.route("/give_permission", methods=['POST'])
def give_permission():
    global permission
    permission_from_coordinator = request.json['permission']
    if permission_from_coordinator:
        permission = True
        print("Permission granted")
    return {}

def get_user(user):
    (ip, port) = const.registry[user]
    return f"http://{ip}:{port}"

def request_score():
    wait_for_permission()
    response = requests.get(f"http://{const.CHAT_SERVER_HOST}:{const.CHAT_SERVER_PORT}/get_score")
    print(f"current score: {response.json()['score']}")
    release_permission()

def start_server(i_am):
    (ip, port) = const.registry[i_am]
    app.run(host=ip, port=port)

def update_score():
    request_score()
    wait_for_permission()
    new_score = input("Enter new score: ")
    try:
        response = requests.post(f"http://{const.CHAT_SERVER_HOST}:{const.CHAT_SERVER_PORT}/update_score", json={"score": new_score})
        print(f"new score: {response.json()['score']}")
        print("Score updated successfully")
    except:
        print(response.json()['error'])
    finally:
        release_permission()

def wait_for_permission():
    global permission
    if not permission:
        requests.post(f"{get_user(coordnator_name)}/get_permission", json={"user": i_am})
    while permission == False:
        sleep(1)
        print("Waiting for permission...")
    return True

def release_permission():
    global permission
    permission = False
    requests.post(f"{get_user(coordnator_name)}/release_permission", json={"user": i_am})

options = {
    "1": request_score,
    "2": update_score,
    "3": exit
}

if __name__ == "__main__":
    i_am = str(sys.argv[1])
    coordnator_name = str(sys.argv[2])

    if i_am == coordnator_name:
        coordinator = True
        print("I am coordinator")
    threading.Thread(target=start_server, args=(i_am,), daemon=True).start()
    while True:
        print("--------------------------------------------------------------------------------")
        print("1. Get Score")
        print("2. Update Score")
        print("3. Exit")
        option = input("Choose an option: ")
        print("--------------------------------------------------------------------------------")
        if option not in options:
            print("Invalid option")
            continue
        os.system('cls||clear')
        options[option]()