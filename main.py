from Crypto.Cipher import AES
from base64 import b64encode
from pprint import pprint
import asyncio
import aiohttp

_pad = lambda s: s + bytes([AES.block_size - len(s) % AES.block_size]) * (AES.block_size - len(s) % AES.block_size)
encrypt = lambda message, key, iv: AES.new(key, AES.MODE_CBC, iv).encrypt(message)

ENDPOINT = 'https://mydtu.duytan.edu.vn/Modules/regonline/ajax/RegistrationProcessing.aspx/AddClassProcessing'

# Retrieving by extract it from cookie in request header
sessionId = 'olnxxdudnd51jcsiad3z0va9'

classRegCodes = [     # Mã đăng kí môn
    'ABC123456789012',
    'ABC123456789012',
    'ABC123456789012',
]

# All the variables below are getting from this following link:
# https://mydtu.duytan.edu.vn/sites/index.aspx?p=home_registeredall&semesterid=68&yearid=65
#
# Inspecting the 'Đăng ký' button to see the year, semester, studentIdNumber and curriculumId in the respective way.
# 
# For example:
# Add_Click('Bạn có muốn Đăng ký Lớp này?',65,67,242XXXXXXXX,'611','AMINHAKEYTEM32NYTES1234567891234','7061737323313233')
# So this does mean:
# + year = '65'
# + semester = '67'
# + studentIdNumber = '242XXXXXXXX'
# + curriculumId = '611'
year = '65'                     # 2019 - 2020
semester = '68'                 # HK Hè
studentIdNumber = '242XXXXXXXX' # Mã số sinh viên
curriculumId = '611'            # 611 - K24TMT
# You also need to enter the captcha once in the above link
# Don't try to refreshing the link because it will alter the captcha in the user's session
captcha = '6969'

async def registerAsync(loop: asyncio, classRegCodes: list) -> list:
    async def doRegister(session: aiohttp.ClientSession, classRegCode: str) -> tuple:
        if not classRegCode:
            return

        params = _pad(','.join([classRegCode, year, semester, studentIdNumber, curriculumId, captcha]).encode())

        encryptedString = encrypt(params, b'AMINHAKEYTEM32NYTES1234567891234', b'7061737323313233')
        encryptedString = b64encode(encryptedString).decode()

        res = await session.post(ENDPOINT, json={
            'encryptedPara': encryptedString
        })
        res = await res.json()
        if 'd' not in res:
            return res, classRegCode

        return res['d'], classRegCode

    session = aiohttp.ClientSession(cookies={'ASP.NET_SessionId': sessionId})
    result = await asyncio.gather(*[doRegister(session, classRegCode) for classRegCode in classRegCodes])
    await session.close()

    return result

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(registerAsync(loop, classRegCodes))
    pprint(result)
