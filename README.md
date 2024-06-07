Asynchronous event-driven channeling for fun

```python
import asyncio
from async_channels import MPSCChannel

channel = MPSCChannel[int]()

@channel.consumer
async def consumer_printer(event: int):
    print(event)

async def main():
    await channel.send(5)
    await channel.run_consumer()

asyncio.run(main())
```