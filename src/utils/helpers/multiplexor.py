from typing import List, Callable, AsyncGenerator, Dict, Tuple
import logging
import asyncio

async def _queue_to_generator(queue: asyncio.Queue, queue_event: asyncio.Event, finish_event: asyncio.Event):
    while True:
        await queue_event.wait()
        if queue.empty():
            queue_event.clear()
            if finish_event.is_set(): break
        else:
            yield await queue.get()
    
async def _multiplex(in_stream: AsyncGenerator, queue_list: List[asyncio.Queue], queue_event_list: List[asyncio.Event], finish_event: asyncio.Event):
    async for in_d in in_stream:
        for q in queue_list:
            await q.put(dict(in_d))
        for qe in queue_event_list:
            qe.set()
            
    for qe in queue_event_list:
        qe.set()
    finish_event.set()
        
def multiplexor(
    func_d: Dict[str, Callable[[AsyncGenerator], AsyncGenerator | None]],
    in_stream: AsyncGenerator
) -> Tuple[Dict[str, AsyncGenerator], asyncio.Task]:
    queue_list: List[asyncio.Queue] = list()
    queue_event_list: List[asyncio.Event] = list()
    stream_end_event = asyncio.Event()
    
    result_d = dict()
    for fun_key in func_d:
        q = asyncio.Queue()
        q_event = asyncio.Event()
        agen = func_d[fun_key](_queue_to_generator(q,q_event,stream_end_event))
        result_d[fun_key] = agen
        queue_list.append(q)
        queue_event_list.append(q_event)
        
    multi_task = asyncio.create_task(_multiplex(in_stream, queue_list, queue_event_list, stream_end_event))
    
    return result_d, multi_task