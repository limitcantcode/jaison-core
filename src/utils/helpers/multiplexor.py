from typing import List, Callable, AsyncGenerator, Dict, Tuple
import asyncio

async def _queue_to_generator(queue: asyncio.Queue):
    try:
        while True:
            next_item = await queue.get()
            yield next_item
    except:
        pass
    
async def _multiplex(in_stream: AsyncGenerator, queue_list: List[asyncio.Queue]):
    async for in_d in in_stream:
        for q in queue_list:
            await q.put(in_d)
            
    for q in queue_list:
        q.shutdown()
        
def multiplexor(
    func_d: Dict[str, Callable[[AsyncGenerator], AsyncGenerator | None]],
    in_stream: AsyncGenerator
) -> Tuple[Dict[str, AsyncGenerator], asyncio.Task]:
    queue_list: List[asyncio.Queue] = list()
    
    result_d = dict()
    for fun_key in func_d:
        q = asyncio.Queue()
        agen = func_d[fun_key](_queue_to_generator(q))
        result_d[fun_key] = agen
        queue_list.append(q)
        
    multi_task = asyncio.create_task(_multiplex(in_stream, queue_list))
    
    return result_d, multi_task