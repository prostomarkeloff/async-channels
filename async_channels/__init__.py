"""
Asynchronous event-driven channeling for fun

async def listener_printer(event: MyEvent):
    print(event.value)

async def sender(ch: Channel[MyEvent]):
    while True:
        ch.send_all(MyEvent(value=5))
        await asyncio.sleep(3)

ch = Channel[MyEvent]()
ch.add_listener(listener_printer, name="printer")
asyncio.create_task(sender(ch))
while True:
    await asyncio.sleep(0)
"""

import typing

EventT = typing.TypeVar("EventT")
ListenerT = typing.Callable[[EventT], typing.Awaitable[None]]


class Channel(typing.Generic[EventT]):
    def __init__(self):
        self._listeners: typing.Dict[str, ListenerT] = {}

    def listener(self, name: typing.Union[str, None] = None):
        def wrapper(coro: ListenerT):
            async def inner(event: EventT):
                return await coro(event)

            self.add_listener(inner, name or coro.__name__)
            return inner
        return wrapper

    def add_listener(self, listener: ListenerT, name: str):
        self._listeners[name] = listener

    async def send_all(self, event: EventT):
        for _, listener in self._listeners.items():
            await listener(event)

    async def send_to(self, event: EventT, name: str):
        await self._listeners[name](event)
