from blobchain.peer import BlobNode
import asyncio
import sys

port = int(sys.argv[1])
if len(sys.argv) == 2:
    host = None
else:
    host = str(sys.argv[2])

asyncio.run(BlobNode(port, host).main())
