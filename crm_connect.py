#!/usr/bin/python3

from aiohttp import web
import mysql_connect
import originate_ami
import time


async def all_handler(request):
    data = await request.post()
    log_write(data)
    # проверяем метод, который получили и сохраняем значения номеров:
    if data["method"] == 'make_call':
        operator = f"{data['employee_phone_number']}"
        # проверяем длину внутреннего номера
        if len(data["employee_phone_number"]) < 6:
            # проверяем длину вызываемого номера, тут далее обязательно должен быть return, для корректного выхода
            if len(data['contact_phone_number']) == 11:
                #тут надо вставить установку на паузу для employee_phone_number?
                # проверяем, что первый символ вызываемого номера 7, меняем на 8 и делаем originate
                if data['contact_phone_number'][0] == '7':
                    number = f"8{data['contact_phone_number'][1:]}"
                    originate_ami.originate(operator, number)
                    return good_request_call()
                # проверяем, что первый символ вызываемого номера 8, ничего не меняем и делаем originate
                elif data['contact_phone_number'][0] == '8':
                    number = f"{data['contact_phone_number']}"
                    originate_ami.originate(operator, number)
                    return good_request_call()
                else:
                    return bad_request("bad outgoing full number without 7 or 8")
            else:
                return bad_request("len outgoing number not 11")
        else:
            return bad_request("len extension 6 or lower")

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
    log_write(response_data)
    return web.json_response(response_data)


def bad_request(reason):
    response_data = {
        "error": 1,
        "data": reason
    }
    log_write(response_data)
    return web.json_response(response_data)


def log_write(payload):
    nowtime = time.strftime('%H:%M:%S')
    #pprint(nowtime + '' + str(payload))
    with open('/var/log/renovation/crmconnect.log', 'a') as file:
        file.write(nowtime + " " + str(payload) + "\n")


def web_server():
    app = web.Application()
    app.add_routes([web.route('*', '/', all_handler)])
    web.run_app(app, host='0.0.0.0', port='8081')

