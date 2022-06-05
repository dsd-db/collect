import os
import time
import json
import asyncio
import threading
from bleak import BleakClient

DEBUG=False
OFFLINE=False

cfg=json.load(open(os.path.join(os.path.dirname(__file__),'collect.json'),'rb'))
alpha=cfg['alpha']
devices=[cfg[i] for i in cfg['collect']]

cache={}
cache_flag={i:False for i in devices}

def f(addr:str,data:bytes)->None:
    assert len(data)==20
    (ox55,ox61,axL,axH,ayL,ayH,azL,azH,wxL,wxH,wyL,wyH,wzL,wzH,RollL,RollH,PitchL,PitchH,YawL,YawH)=data
    assert ox55==0x55
    assert ox61==0x61

    def int2(h:int,l:int)->int:
        ans=(h<<8)|l
        if ans>32767:
            ans-=65536
        return ans

    ax=int2(axH,axL)
    ay=int2(ayH,ayL)
    az=int2(azH,azL)
    wx=int2(wxH,wxL)
    wy=int2(wyH,wyL)
    wz=int2(wzH,wzL)
    Roll=int2(RollH,RollL)
    Pitch=int2(PitchH,PitchL)
    Yaw=int2(YawH,YawL)

    def linear(x:int,k:int)->float:
        return k*x/32768

    ax=linear(ax,16)
    ay=linear(ay,16)
    az=linear(az,16)
    wx=linear(wx,2000)
    wy=linear(wy,2000)
    wz=linear(wz,2000)
    Roll=linear(Roll,180)
    Pitch=linear(Pitch,180)
    Yaw=linear(Yaw,180)

    agx=ax
    agy=ay
    agz=az
    alx=0
    aly=0
    alz=0

    if addr in cache:
        (lax,lay,laz,lwx,lwy,lwz,lRoll,lPitch,lYaw,lalx,laly,lalz,lagx,lagy,lagz)=cache[addr]
        agx=alpha*lagx+(1-alpha)*ax
        agy=alpha*lagy+(1-alpha)*ay
        agz=alpha*lagz+(1-alpha)*az
        alx=ax-agx
        aly=ay-agy
        alz=az-agz

    cache[addr]=(ax,ay,az,wx,wy,wz,Roll,Pitch,Yaw,alx,aly,alz,agx,agy,agz)
    cache_flag[addr]=True



def notification_handler(id):
    def handler(sender,data):
        f(id,data)
    return handler

async def run(id):
    _count=0
    while True:
        try:
            if DEBUG:
                print('BConnect:',id)
            client = BleakClient(id)
            await client.connect()
            await client.start_notify(cfg['imuReadUUID'], notification_handler(id))
            _count=0
        except:
            _count+=1
            if _count>=10:
                if DEBUG:
                    print('BFailed:',id)
                # sys.exit(0)
                OFFLINE=True
                return


async def main():
    tasks=[run(i) for i in devices]
    await asyncio.gather(*tasks)


CSV=os.path.join(os.path.dirname(__file__),'collect.csv')
data=list()
for i in open(CSV,'r').read().split('\n'):
    i=i.split(',')
    data.append(','.join(i[0:30]+i[75:90]).encode('utf8'))
n=len(data)
i=-1

def getmsg()->bytes:
    while not all(cache_flag.values()):
        if OFFLINE:
            break
        time.sleep(0.01)
    if OFFLINE:
        i=(i+1)%n
        return data[i]
    ans=''
    for i in devices:
        ans+=','.join([str(j) for j in cache[i]])
        ans+='\n' if i is devices[-1] else ','
        cache_flag[i]=False
    return ans.encode('utf8')


def con()->None:
    while True:
        print(getmsg().decode('utf8'),flush=True)

threading.Thread(target=con,daemon=True).start()
asyncio.run(main())
