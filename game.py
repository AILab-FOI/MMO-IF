import re
import asyncio
import pexpect as px
import sys
from glulxe.interface import i7Game

from avatar import Avatar

GAME_FILE_NAME = "rooms.gblorb"

game = None
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

async def change_location(response):
    location = get_room_name(response)

    global current_location
    if not location is None and not location is current_location:
        current_location = location

        loop = asyncio.get_event_loop()
        loop.create_task(agent.send_location(location))
        await asyncio.sleep(1)

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

    output = game.next(command)
    print(output)
    # location change
    if 'west' in command or 'east' in command or 'north' in command or 'south' in command:
        await change_location(output)

async def start_agent(jid, password):
    global agent
    agent = Avatar(
        jid,
        password
    )
    agent.start()
    # wait for agent to start up
    await asyncio.sleep(2)

async def start_game():
    global game
    game = i7Game(GAME_FILE_NAME, interactive=False)
    intro = game.intro()
    print(intro)
    await change_location(intro)

async def main(jid, password):
    await start_agent(jid, password)
    await start_game()

    loop = asyncio.get_event_loop()
    while True:
        cmd = input('--> ')

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
    