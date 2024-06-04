Asynchronous event-driven channeling for fun

```python
import asyncio
from async_channels import Channel

channel = Channel[int]()

@channel.listener()
async def listener_printer(event: int):
    print(event)

async def main():
    await channel.send_all(5)

asyncio.run(main())
```