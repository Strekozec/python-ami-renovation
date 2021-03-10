#!/usr/bin/python3

import asyncio
from aiohttp import web
import mysql_connect


async def handler(request):
    data = await request.post()
    # проверяем метод, который получили
    if data["method"] == 'make_call':
        # проверяем длину внутреннего номера
        if len(data["employee_phone_number"]) < 6:
            # проверяем длину вызываемого номера
            if len(data['contact_phone_number']) == 11:
                # проверяем, что первый символ вызываемого номера 7
                if data['contact_phone_number'][0] == '7':
                    number = f"8{data['contact_phone_number'][1:]}"
                    print(number)
                elif data['contact_phone_number'][0] == '8':
                    number = f"{data['contact_phone_number']}"
                    print(number)
                else:
                    bad_request("bad outgoing number without 7 or 8")
            else:
                bad_request("len outgoing number not 11")
            extension = data["employee_phone_number"]
            print(extension)
            # Успешный запрос
            return good_request(None)
        else:
            bad_request("len extension 6 or higher")

    elif data["method"] == 'call_records':
        tyers = 0
        ids = (data['call_id'], data['parent_id'])
        for id in ids:
            result = mysql_connect.call_record(mysql_connect.connection(), id)
            if result == 'error':
                # Если проблема с подключением к БД
                return bad_request("Mysql connection error")
            elif result == 'not found':
                tyers += 1
                if tyers == 2:
                    return bad_request("not found id")
                else:
                    continue
            else:
                return good_request(result)


def good_request(result):
    response_data = {
        "error": 0,
        "data": {
            "file_link": result
        }
    }
    return web.json_response(response_data)


def bad_request(reason):
    response_data = {
        "error": 1,
        "data": reason
    }
    return web.json_response(response_data)


async def main():
    server = web.Server(handler)
    runner = web.ServerRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, '192.168.119.250', 8080)
    await site.start()

    print("======= Serving on http://192.168.119.250:8080/ ======")

    # pause here for very long time by serving HTTP requests and
    # waiting for keyboard interruption
    await asyncio.sleep((24 * 3600) - 1)
    #print(request)


loop = asyncio.get_event_loop()

try:
    print('1')
    loop.run_until_complete(main())
except KeyboardInterrupt:
    pass
loop.close()
