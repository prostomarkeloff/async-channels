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
import asyncio
import typing

EventT = typing.TypeVar("EventT")
ListenerT = typing.Callable[[EventT], typing.Awaitable[None]]


class Channel(typing.Generic[EventT]):
    def __init__(self):
        self._listeners: typing.Dict[str, ListenerT[EventT]] = {}

    def listener(self, name: typing.Union[str, None] = None):
        def wrapper(coro: ListenerT[EventT]):
            async def inner(event: EventT):
                return await coro(event)

            self.add_listener(inner, name or coro.__name__)
            return inner
        return wrapper

    def add_listener(self, listener: ListenerT[EventT], name: typing.Union[None, str] = None):
        self._listeners[name or listener.__name__] = listener

    async def send_all(self, event: EventT, wait_till_complete: bool = False):
        if wait_till_complete:
            tasks = [asyncio.create_task(listener(event)) for _, listener in self._listeners.items()]
            await asyncio.wait(tasks)
        else:
            for _, listener in self._listeners.items():
                await listener(event)

    async def send_to(self, event: EventT, name: str, wait_till_complete: bool = False):
        if wait_till_complete:
            await asyncio.wait([asyncio.create_task(self._listeners[name](event))])
        else:
            _ = asyncio.create_task(self._listeners[name](event))

