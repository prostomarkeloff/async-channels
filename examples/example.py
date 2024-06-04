import asyncio
from async_channels import Channel

channel = Channel[int]()

# use decorator; you could also add name as an argument
@channel.listener()
async def listener_printer(event: int):
    print(event)

async def listener_adding_printer(event: int):
    print(event + 1)

async def sender_plus(channel: Channel[int]):
    await channel.send_to(2, "adder")

async def sender(channel: Channel[int]):
    await channel.send_all(5)


async def main():
    # add with method
    channel.add_listener(listener_adding_printer, "adder")
    await sender(channel)
    await sender_plus(channel)

asyncio.run(main())
