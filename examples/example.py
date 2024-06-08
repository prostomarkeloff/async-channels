from async_channels import MPSCChannel, ListeningSettings
import asyncio

channel = MPSCChannel[str]()

@channel.consumer
async def default_consumer(event: str):
    print("Default consumer got ", event)


async def main():
    await channel.run_consumer()
    # next event won't be sent till this isn't consumed
    # also you can set timeouts to consuming the message; otherwise it would be cancelled
    # and exception is raised
    # nb: default timeout is -1, that means that the event could be waited forever
    try:
        await channel.send("hello world", wait_till_complete=True, timeout=5)
    except asyncio.TimeoutError:
        print("Event was never consumed")
    await channel.send("goodbye")
    await channel.stop_consumer()

    # only two events will be consumed
    await channel.run_consumer(ListeningSettings(forever=False, ticks=2))
    await channel.send("hello2")
    await channel.send("bye")

    # events sent this way will be grouped to one event
    await channel.send("won't", "be get right now")
    await channel.send("never listened to")
    async for event in channel.listen_to(ListeningSettings(forever=False, ticks=1)):
        print("Listened to ", event)

asyncio.run(main())