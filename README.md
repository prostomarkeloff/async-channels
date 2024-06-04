Asynchronous event-driven channeling for fun

```python
import asyncio
from async_channels import Channel

channel = Channel[int]()

@channel.listener()
async def listener_printer(event: int):
    print(event)

async def sender(channel: Channel[int]):
    await channel.send_all(5)

async def main():
    await sender(channel)
```