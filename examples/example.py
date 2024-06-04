import asyncio
from async_channels import Channel

channel = Channel[int]()


# use decorator; you could also add name as an argument
@channel.listener()
async def listener_printer(event: int):
    print(event)


async def listener_adding_printer(event: int):
    print(event + 1)


@channel.listener("awaiter")
async def listener_print_after(event: int):
    print(event + 10)
    await asyncio.sleep(10)


async def main():
    # add with method
    channel.add_listener(listener_adding_printer, "adder")
    await channel.send_to(5, "listener_printer")
    await channel.send_to(5, "adder")
    # code below won't run till sending (and listening inside) won't be complete
    await channel.send_to(5, "awaiter", wait_till_complete=True)
    await channel.send_all(5)


asyncio.run(main())
