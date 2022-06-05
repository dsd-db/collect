import os
import json
import asyncio
from bleak import BleakScanner

async def main():
    for d in await BleakScanner.discover():
        print(d)

asyncio.run(main())

'''
D1:7A:2A:54:02:95: WT901-L1
D7:0F:4F:1D:4F:B5: WT901-L2
E8:67:FE:A6:D4:3C: WT901-R3
'''

cfg={
    'collect':['WT901-L1','WT901-L2','WT901-R3'],
    'WT901-L1':'D1:7A:2A:54:02:95',
    'WT901-L2':'D7:0F:4F:1D:4F:B5',
    'WT901-R3':'E8:67:FE:A6:D4:3C',
    'imuReadUUID':      '0000FFE4-0000-1000-8000-00805F9A34FB',
    'imuServiceUUID':   '0000FFE5-0000-1000-8000-00805F9A34FB',
    'imuWriteUUID':     '0000FFE9-0000-1000-8000-00805F9A34FB',
    'alpha':0.8
}
for i in cfg['collect']:
    assert i in cfg
open(os.path.join(os.path.dirname(__file__),'collect.json'),'w').write(json.dumps(cfg,skipkeys=True,ensure_ascii=True,indent=4,sort_keys=True))
