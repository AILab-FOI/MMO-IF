import re
import asyncio
import os
import tempfile
import pexpect as px
import sys

from avatar import Avatar

GAME_FILE_NAME = "rooms.gblorb"

asc_re = re.compile(r"\\x[0-9a-h\)\[;rml\?HJM]+")
tmpdir = tempfile._get_default_tempdir()
tmpfile = os.path.join(tmpdir, next(tempfile._get_candidate_names()))

game = None
last = 0
llast = 0

current_location = None

EXIT_COMMANDS = ["quit", "exit"]

ROOM_SELECTION_PATTERN = 'You entered (.*) room'
MESSAGE_PARAMS_PATTERN = '@([^\s]+) (.*)'

agent = None

def get_room_name(response):
    if match := re.search(ROOM_SELECTION_PATTERN, response, re.IGNORECASE):
        return match.group(1)

    return None

def get_message_params(response):
    if match := re.search(MESSAGE_PARAMS_PATTERN, response, re.IGNORECASE):
        receiver = match.group(1)
        message = match.group(2)
        if not receiver is None and not message is None:
            return (receiver, message)

    return None

def clean(string):
    string = string.replace(r"\r", r"\n")
    string = asc_re.sub(r"", string)
    return eval(string).decode()

async def change_location(response):
    location = get_room_name(response)

    global current_location
    if not location is None and not location is current_location:
        current_location = location

        loop = asyncio.get_event_loop()
        loop.create_task(agent.send_location(location))
        await asyncio.sleep(1)

async def print_game_response():
    global game, last, llast

    game.sendline(" ")
    f = open(tmpfile, "rb")
    new = [x for x in enumerate(f.readlines())][last:]
    for n, i in new:
        line = clean(str(i)).split("\n")
        previous = ""
        exline = [i for i in enumerate(line)][llast + 1 :]
        for m, l in exline:
            if "I beg your pardon?" in l and previous == "> ":
                continue
            previous = l
            if l[0] == ">":
                continue

            await change_location(l)
            print(l)
            llast = m
    f.close()
    f.close()

    print("\n")

def start_game(file_name):
    file = open(tmpfile, "wb")
    file.close()

    global game
    game = px.spawn("/bin/bash -c 'glulxe \"%s\" > %s'" % (file_name, tmpfile))
    game.setecho(False)


async def send_message_to_player(command):
    try:
        (player, message) = get_message_params(command)        
        await agent.send_msg(player, message)
    except:
        pass

async def process_command(command):
    # is communication
    if command.startswith('@'):
        await send_message_to_player(command)

        return

    # process valid commands    
    game.sendline(command)

async def main(jid, password):
    start_game(GAME_FILE_NAME)

    global agent
    agent = Avatar(
        jid,
        password
    )
    agent.start()
    # wait for agent to start up
    await asyncio.sleep(3)

    loop = asyncio.get_event_loop()
    while True:
        await print_game_response()
        cmd = input()

        if cmd in EXIT_COMMANDS:
            break

        loop.create_task(process_command(cmd.lower()))
        await asyncio.sleep(1)


if __name__ == "__main__":
    if len(sys.argv) == 3:
        jid = sys.argv[1]
        password = sys.argv[2]

        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(jid, password))
    