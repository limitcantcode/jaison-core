CHUNK_SIZE = 4096

async def list_to_agen(target_list):
    for item in target_list:
        yield item
        
        
def chunk_buffer(buf):
    chunks = list()
    while len(buf) > 0:
        chunks.append(buf[:CHUNK_SIZE])
        buf = buf[CHUNK_SIZE:]
        
    return chunks