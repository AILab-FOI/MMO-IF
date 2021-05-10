import re
import asyncio
import os
import tempfile
import pexpect as px

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

def change_location(response):
    location = get_room_name(response)

    if not location is None:
        global current_location
        current_location = location

def print_game_response():
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

            change_location(l)
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


def send_message_to_player(command):
    try:
        (player, message) = get_message_params('@everyone asd')

        print(f'Sending message to {player} with content {message}')
    except:
        pass

def process_command(command):
    # is exit command?
    if command in EXIT_COMMANDS:
        return True

    # is communication
    if command.startswith('@'):
        send_message_to_player(command)

        return False

    # process valid commands    
    game.sendline(command)

    return False

async def main():
    start_game(GAME_FILE_NAME)

    while True:
        print_game_response()
        cmd = input()

        should_exit = process_command(cmd.lower())

        if should_exit:
            break

if __name__ == "__main__":
    asyncio.run(main())
    