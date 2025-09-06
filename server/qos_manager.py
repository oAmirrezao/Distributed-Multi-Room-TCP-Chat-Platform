import asyncio
import heapq
from dataclasses import dataclass, field
from typing import Any
from common.protocol import Priority

@dataclass(order=True)
class PriorityItem:
    priority: int
    count: int = field(compare=False)
    func: Any = field(compare=False)
    args: Any = field(compare=False)
    kwargs: Any = field(compare=False)

class QoSManager:
    def __init__(self, max_concurrent=10):
        self.queues = {
            Priority.CRITICAL: [],
            Priority.HIGH: [],
            Priority.NORMAL: [],
            Priority.LOW: []
        }
        self.max_concurrent = max_concurrent
        self.current_tasks = 0
        self.counter = 0
        self.lock = asyncio.Lock()
    
    async def enqueue(self, func, *args, priority=Priority.NORMAL, **kwargs):
        async with self.lock:
            self.counter += 1
            item = PriorityItem(
                priority=-priority.value,  # Higher priority = lower number
                count=self.counter,
                func=func,
                args=args,
                kwargs=kwargs
            )
            heapq.heappush(self.queues[priority], item)
        
        asyncio.create_task(self._process_queue())
    
    async def _process_queue(self):
        async with self.lock:
            if self.current_tasks >= self.max_concurrent:
                return
            
            # Find highest priority non-empty queue
            for priority in [Priority.CRITICAL, Priority.HIGH, Priority.NORMAL, Priority.LOW]:
                if self.queues[priority]:
                    item = heapq.heappop(self.queues[priority])
                    self.current_tasks += 1
                    
                    asyncio.create_task(self._execute_task(item))
                    break
    
    async def _execute_task(self, item):
        try:
            await item.func(*item.args, **item.kwargs)
        finally:
            async with self.lock:
                self.current_tasks -= 1
            
            # Process next item
            asyncio.create_task(self._process_queue())
