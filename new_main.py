from typing import List
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad as pkcs7_pad
from base64 import b64encode
from pprint import pprint
from time import sleep
import asyncio
import aiohttp
import os

class Account:
    def __init__(self, classRegCodes:List[str], studentIdNumber:str) -> None:
        self.classRegCodes = classRegCodes
        self.studentIdNumber = studentIdNumber

    def getClassRegCodes(self):
        return self.classRegCodes

    def getStudentIdNumber(self):
        return self.studentIdNumber

class DTURegister:
    ENDPOINT = 'https://mydtu.duytan.edu.vn/Modules/regonline/ajax/RegistrationProcessing.aspx/AddClassProcessing'

    def __init__(self, sessionId, year, semester, curriculumId, captcha) -> None:
        self.sessionId = sessionId
        self.year = year
        self.semester = semester
        self.curriculumId = curriculumId
        self.captcha = captcha

    @staticmethod
    def aes_encrypt(iv, key, message):
        return AES.new(key, AES.MODE_CBC, iv).encrypt(message)

    async def doRegister(self, session: aiohttp.ClientSession, classRegCode: str, studentIdNumber: str) -> tuple:
        registerSeq = ','.join([classRegCode, self.year, self.semester, studentIdNumber, self.curriculumId, self.captcha]).encode()
        registerSeq = pkcs7_pad(registerSeq, AES.block_size)

        encryptedString = self.aes_encrypt(b'7061737323313233', b'AMINHAKEYTEM32NYTES1234567891234', registerSeq)
        encryptedString = b64encode(encryptedString).decode()

        res = await session.post(DTURegister.ENDPOINT, cookies={
            'ASP.NET_SessionId': self.sessionId
        }, json={
            'encryptedPara': encryptedString
        })
        res = await res.json()
        if 'd' not in res:
            return res, classRegCode, studentIdNumber

        return res['d'], classRegCode, studentIdNumber

    async def doAccountRegister(self, session: aiohttp.ClientSession, account: Account) -> list:
        classRegCodes = account.getClassRegCodes()
        studentIdNumber = account.getStudentIdNumber()
        result = await asyncio.gather(*[self.doRegister(session, classRegCode, studentIdNumber) for classRegCode in classRegCodes])
        return result

    async def run(self, accounts:List[Account]):
        session = aiohttp.ClientSession()
        result = await asyncio.gather(*[self.doAccountRegister(session, account) for account in accounts])
        await session.close()
        return result

if __name__ == "__main__":
    accounts = [
        Account(
            classRegCodes=['RegisterClassCode0','RegisterClassCode1','RegisterClassCode2'],
            studentIdNumber='17654288917'
        ),
        # you can add another account here.
    ]

    runner = DTURegister(
        sessionId='sqydqiq1bptgoklmhw1timms',
        year='65',
        semester='68',
        curriculumId='611',
        captcha='OKOK'
    )
    while True:
        result = asyncio.run(runner.run())
        pprint(result)
        sleep(5) # Slow it down, don't be intensive!!!
        os.system('clear') # This shit is need to change depending on the OS :D

