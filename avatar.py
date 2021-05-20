from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message

import settings

class Avatar(Agent):
    class ReceiveMessage(CyclicBehaviour):
        async def run(self):
            msg = await self.receive()
            if msg:
                print(msg.body)
             
    class SendMessage(CyclicBehaviour):
        async def run(self):
            pass

    class PresenceSetup(OneShotBehaviour):

        def on_subscribe(self, jid):
            self.presence.approve(jid)


        async def run(self):
            self.presence.on_subscribe = self.on_subscribe

            self.presence.set_available()

            self.presence.subscribe(settings.SERVER_JID)

    async def setup(self):
        self.add_behaviour(self.PresenceSetup())

        self.add_behaviour(self.ReceiveMessage())

        self.send_msg_behav = self.SendMessage()
        self.add_behaviour( self.send_msg_behav )

    async def send_location(self, location):
        msg = Message(to=settings.SERVER_JID)
        msg.set_metadata('action', 'location')
        msg.body = location
        
        await self.send_msg_behav.send(msg)

    async def send_msg(self, to, message):
        msg = Message(to=settings.SERVER_JID)
        msg.set_metadata('action', 'send_message')
        msg.set_metadata('to', to)
        msg.body = message

        await self.send_msg_behav.send(msg)

    def stop(self):
        self.presence.unsubscribe(settings.SERVER_JID)

        super().stop()

