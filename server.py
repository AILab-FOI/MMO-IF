from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message
from spade.template import Template
import time

import settings

class Server(Agent):
    def __init__( self, name, password ):
        super().__init__( name, password )
        
        self.players = {}

    class PresenceSetup(OneShotBehaviour):
        def on_subscribe(self, jid):
            self.presence.approve(jid)
            self.presence.subscribe(jid)

        def on_unsubscribe(self, jid):
            self.presence.approve(jid)

        async def run(self):
            self.presence.on_subscribe = self.on_subscribe
            self.presence.on_unsubscribe = self.on_unsubscribe
            
            self.presence.set_available()

    class ForwardMessage(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=1)
            
            if not msg:
                return

            body = msg.body
            sender = msg.sender.localpart
            to = msg.metadata['to']
            sender_location = self.agent.players[sender]

            if not to:
                return

            for player in self.agent.players:
                if not player in self.agent.get_contacts_simple():
                    continue

                player_location = self.agent.players[player]

                if player_location == sender_location and not player == sender:
                    if to == 'everyone' or to == player:
                        msg = Message(to=f'{player}@{settings.XMPP_SERVER}')                    
                        msg.body = f'{sender} said: {body}.'

                        await self.send(msg)

    class LocationChange(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=1)
            
            if not msg:
                return

            current_location = msg.body
            current_player = msg.sender.localpart

            self.agent.players[current_player] = current_location

            for player in self.agent.players:
                if not player in self.agent.get_contacts_simple():
                    continue

                player_location = self.agent.players[player]

                if player_location == current_location and not player == current_player:
                    msg = Message(to=f'{player}@{settings.XMPP_SERVER}')
                    msg.body = f'{current_player} has entered {current_location} room.'
                    
                    await self.send(msg)

    async def setup(self):
        self.add_behaviour(self.PresenceSetup())

        self.forward_template = Template()
        self.forward_template.set_metadata('action','send_message')
        self.add_behaviour(self.ForwardMessage(), self.forward_template)

        self.location_template = Template()
        self.location_template.set_metadata('action','location')
        self.add_behaviour(self.LocationChange(), self.location_template)

    def get_contacts_simple(self):
        return [
            str(jid)
            for jid in self.presence.get_contacts().keys() 
        ]

    def stop(self):
        for contact in self.presence.get_contacts().keys():
            self.presence.unsubscribe(str(contact))

        super().stop()

if __name__ == '__main__':
    server = Server(
        settings.SERVER_JID,
        settings.SERVER_PASS
    )
    server.start()

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
    
    server.stop()

