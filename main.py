from Crypto.Cipher import AES
from base64 import b64encode as base64_encode
from pprint import pprint
from time import sleep
import asyncio
import aiohttp
import os

pkcs7_padding = lambda s: s + bytes([AES.block_size - len(s) % AES.block_size]) * (AES.block_size - len(s) % AES.block_size)
AES_encrypt = lambda message, key, iv: AES.new(key, AES.MODE_CBC, iv).encrypt(message)

TEMP_ENDPOINT = 'https://mydtu.duytan.edu.vn/Modules/regonline/ajax/LoadCaptcha.aspx/Temp'
ENDPOINT = 'https://mydtu.duytan.edu.vn/Modules/regonline/ajax/RegistrationProcessing.aspx/AddClassProcessing'
accounts = []

year = '65'      # 2019 - 2020
semester = '68'  # Học kì Hè

def addAccount(**kwargs):
    kwargs.update(year=year, semester=semester)
    accounts.append(kwargs)

async def registerAsync(loop: asyncio, accounts: list) -> list:
    async def doRegister(session: aiohttp.ClientSession, classRegCode: str, **kwargs) -> tuple:
        sessionId = kwargs['sessionId']
        year = kwargs['year']
        semester = kwargs['semester']
        studentIdNumber = kwargs['studentIdNumber']
        curriculumId = kwargs['curriculumId']
        captcha = kwargs['captcha']

        params = pkcs7_padding(','.join([classRegCode, year, semester, studentIdNumber, curriculumId, captcha]).encode())

        encryptedString = AES_encrypt(params, b'AMINHAKEYTEM32NYTES1234567891234', b'7061737323313233')
        encryptedString = base64_encode(encryptedString).decode()

        while True:
            try:
                # pre-check step
                res = await session.post(TEMP_ENDPOINT, cookies={
                    'ASP.NET_SessionId': sessionId
                }, json={
                    'termVal': classRegCode
                })
                json = await res.json()
                if 'd' not in json or json['d'] != '1':
                    return json, classRegCode, studentIdNumber

                res = await session.post(ENDPOINT, cookies={
                    'ASP.NET_SessionId': sessionId
                }, json={
                    'encryptedPara': encryptedString
                })
                json = await res.json()
                if 'd' not in json:
                    return json, classRegCode, studentIdNumber

                return json['d'], classRegCode, studentIdNumber
            except:
                continue

    async def doAccountRegister(session: aiohttp.ClientSession, account: dict) -> list:
        classRegCodes = account['classRegCodes']
        return await asyncio.gather(*[doRegister(session, classRegCode, **account) for classRegCode in classRegCodes])


    session = aiohttp.ClientSession()
    result = await asyncio.gather(*[doAccountRegister(session, account) for account in accounts])
    await session.close()

    return result

if __name__ == '__main__':
    addAccount(
        sessionId='sqydqiq1bptgoklmhw1timms',
        classRegCodes=['ABC123456789012', 'DEF123456789012', 'GHI123456789012'],
        studentIdNumber='24123456789',
        curriculumId='611',
        captcha='3976'
    )

    # You can add more addAccount() here

    loop = asyncio.get_event_loop()
    while True:
        result = loop.run_until_complete(registerAsync(loop, accounts))
        pprint(result)

        sleep(5) # Slow it down, don't be intensive!!!
        os.system('clear') # This shit is need to change depending on the OS