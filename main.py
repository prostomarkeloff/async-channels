from typing import List, Generic, TypeVar, Callable, Awaitable
from dataclasses import dataclass
import asyncio
import random

MessageT = TypeVar("MessageT")
AnswerT = TypeVar("AnswerT")

@dataclass
class Answer(Generic[AnswerT]):
    receiver_name: str
    answer: AnswerT

ReceiverCallable = Callable[[MessageT], Awaitable[Answer[AnswerT]]]

class Receiver(Generic[MessageT, AnswerT]):
    def __init__(self, name: str, receiver: ReceiverCallable[MessageT, AnswerT]) -> None:
        self.name = name
        self.receiver = receiver

    async def receive(self, message: MessageT) -> Answer[AnswerT]:
        return Answer(self.name, await self.receiver(message))

def receiver(name: str):
    def decorator(r: ReceiverCallable):
        ar = Receiver(name, r)
        async def wrapper(message: MessageT):
            return await ar.receive(message)
        return wrapper
    return decorator

class Channel(Generic[MessageT, AnswerT]):
    """
    T: type of message
    """
    def __init__(self) -> None:
        self._receivers: List[Receiver[MessageT, AnswerT]] = []
        self._answers: List[Answer[AnswerT]] = []

    def add_receiver(self, receiver: Receiver):
        self._receivers.append(receiver)

    async def _send(self, message: MessageT, receiver: Receiver):
        self._answers.append(await receiver(message))

    async def send(self, message: MessageT):
        for receiver in self._receivers:
            asyncio.create_task(self._send(message, receiver))

    async def listen(self):
        while True:
            if len(self._answers):
                yield self._answers.pop()
            await asyncio.sleep(0)

@receiver("receiver1")
async def receiver1(message: int) -> int:
    return message + 1

@receiver("receiver2")
async def receiver2(message: int) -> int:
    return message + 2

async def message_sender(channel: Channel[int, Answer[int]]):
    while True:
        await channel.send(random.randint(1, 100))
        await asyncio.sleep(5)

async def main():
    channel = Channel[int, Answer[int]]()
    channel.add_receiver(receiver1)
    channel.add_receiver(receiver2)
    asyncio.create_task(message_sender(channel))
    async for answer in channel.listen():
        print(f"Answer from {answer.receiver_name} is: {answer.answer}")

asyncio.run(main())
