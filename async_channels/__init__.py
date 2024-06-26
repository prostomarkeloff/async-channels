"""
Asynchronous event-driven channeling for fun
"""
import asyncio
import typing
import dataclasses

EventT = typing.TypeVar("EventT")
ConsumerT = typing.Callable[[EventT], typing.Awaitable[None]]


class _InternalEvent(typing.Generic[EventT]):
    def __init__(self, events: typing.List[EventT], wait: bool, timeout: int):
        self.completed = not wait
        self.events = events
        self.timeout = timeout # -1 means there is no timeout (we can wait forever)


    def __iter__(self):
        return self

    def __next__(self):
        while self.events:
            return self.events.pop(0)
        raise StopIteration()

    async def wait(self):
        while not self.completed and self.timeout == -1:
            await asyncio.sleep(0)
        while not self.completed and self.timeout > 0:
            self.timeout -= 1
            await asyncio.sleep(1)
        if self.timeout == 0:
            self.completed = True # cancellation
            raise asyncio.TimeoutError()
        return


@dataclasses.dataclass
class ListeningSettings:
    forever: bool = True
    ticks: int = -1  # ticks = -1 means that it could be listened forever

    def __post_init__(self):
        if self.forever and self.ticks > -1: raise ValueError("Eternity couldn't be ticked")
        if self.ticks == 0: raise ValueError("Ticks == 0 means nothing (no listening at all)")
        if not self.forever and self.ticks < 1: raise ValueError(
            "Forever = False and ticks < 1 means nothing (no listening at all)")


class MPSCChannel(typing.Generic[EventT]):
    def __init__(self, consumer: typing.Union[ConsumerT, None] = None):
        self._consuming_lock = asyncio.Lock()
        self._consumer = consumer
        self._events: typing.List[_InternalEvent[EventT]] = []
        self._current_task: typing.Union[asyncio.Task, None] = None

    def consumer(self, coro: ConsumerT):
        self._consumer = coro

        async def coro(event: EventT):
            return await coro(event)

        return coro

    async def send(self, *events: EventT, wait_till_complete: bool = False, timeout: int = -1):
        if not wait_till_complete and timeout > 0: raise ValueError("Timeouts can't be used without waiting to complete")
        event = _InternalEvent(list(events), wait_till_complete, timeout)
        self._events.append(event)
        if wait_till_complete:
            await event.wait()
        return

    async def _consumer_runner(self, settings: ListeningSettings):
        if settings.forever:
            while self._consuming_lock.locked():
                if self._events:
                    internal_event = self._events.pop(0)
                    if internal_event.completed: continue
                    for event in internal_event:
                        await self._consumer(event)
                    internal_event.completed = True
                else:
                    await asyncio.sleep(0)
            else:
                return
        else:
            while self._consuming_lock.locked():
                while settings.ticks > 0:
                    if self._events:
                        internal_event = self._events.pop(0)
                        if internal_event.completed: continue
                        for event in internal_event:
                            await self._consumer(event)
                        internal_event.completed = True
                        settings.ticks -= 1
                    else:
                        await asyncio.sleep(0)
                else:
                    self._consuming_lock.release()
                    return await self._stop_consumer_inner()
            else:
                return

    async def run_consumer(self, settings: typing.Union[ListeningSettings, None] = None):
        if not self._consumer: raise RuntimeError("Consumer is not set")
        if settings is None: settings = ListeningSettings()
        if self._consuming_lock.locked():
            raise RuntimeError("This channel is already listened to")

        await self._consuming_lock.acquire()
        runner = asyncio.create_task(self._consumer_runner(settings))
        self._current_task = runner

    async def _stop_consumer_inner(self):
        while self._events:
            await asyncio.sleep(0)
        self._current_task.cancel()
        self._consuming_lock.release()
    async def stop_consumer(self):
        if not self._consuming_lock.locked(): raise RuntimeError("No consumer is running")
        await self._stop_consumer_inner()

    async def listen_to(self, settings: typing.Union[ListeningSettings, None] = None):
        if settings is None: settings = ListeningSettings(True, 0)
        if self._current_task and not self._current_task.done():
            await asyncio.sleep(0)
        if self._consuming_lock.locked():
            raise RuntimeError("This channel is already listened to")

        await self._consuming_lock.acquire()
        if settings.forever:
            while self._consuming_lock.locked():
                if self._events:
                    internal_event = self._events.pop(0)
                    if internal_event.completed: continue
                    for event in internal_event:
                        yield event
                    internal_event.completed = True
                else:
                    await asyncio.sleep(0)
            else:
                return
        else:
            while self._consuming_lock.locked():
                while settings.ticks > 0:
                    if self._events:
                        internal_event = self._events.pop(0)
                        if internal_event.completed: continue
                        for event in internal_event:
                            yield event
                        internal_event.completed = True
                        settings.ticks -= 1
                    else:
                        await asyncio.sleep(0)
                else:
                    self._consuming_lock.release()
                    break
            else:
                return


__all__ = (
    "ListeningSettings",
    "MPSCChannel"
)
