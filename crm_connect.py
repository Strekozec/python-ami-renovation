#!/usr/bin/python3

from aiohttp import web
import mysql_connect


async def all_handler(request):
    data = await request.post()
    # проверяем метод, который получили и сохраняем значения номеров:
    if data["method"] == 'make_call':
        number = f"8{data['contact_phone_number'][1:]}"
        operator = f"{data['employee_phone_number']}"
        # проверяем длину внутреннего номера
        if len(data["employee_phone_number"]) < 6:
            # проверяем длину вызываемого номера, тут далее обязательно должен быть return, для корректного выхода
            if len(data['contact_phone_number']) == 11:
                # проверяем, что первый символ вызываемого номера 7, здесь работаем с сохраненными номерами
                #
                #
                #
                #
                if data['contact_phone_number'][0] == '7':
                    return good_request_call()
                elif data['contact_phone_number'][0] == '8':
                    return good_request_call()
                else:
                    return bad_request("bad outgoing full number without 7 or 8")
            else:
                return bad_request("len outgoing number not 11")
        else:
            return bad_request("len extension 6 or higher")

    elif data["method"] == 'call_records':
        tyers = 0
        ids = (data['call_id'], data['parent_id'])
        for id in ids:
            result = mysql_connect.call_record(mysql_connect.connection(), id)
            if result == 'error':
                # Если проблема с подключением к БД
                return bad_request("Mysql connection error")
            elif result == None:
                tyers += 1
                if tyers == 2:
                    return bad_request("not found id")
                else:
                    continue
            else:
                return good_request(result)


def good_request_call():
    response_data = {
        "error": 0,
        "data": None
    }
    return web.json_response(response_data)


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


def web_server():
    app = web.Application()
    app.add_routes([web.route('*', '/', all_handler)])
    web.run_app(app, host='0.0.0.0', port='8081')

