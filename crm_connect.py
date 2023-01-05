#!/usr/bin/python3

from aiohttp import web
import mysql_connect
import originate_ami
import logs
import os
import time


async def all_handler(request):
    data = await request.post()
    logs.log_write('crmconnect', data, None)
    # проверяем метод, который получили и сохраняем значения номеров:
    if data["method"] == 'make_call':
        operator = str(f"{data['employee_phone_number']}")
        # проверяем длину внутреннего номера
        if len(data["employee_phone_number"]) < 6:
            # проверяем длину вызываемого номера, тут далее обязательно должен быть return, для корректного выхода
            if len(data['contact_phone_number']) == 11:
                #тут надо вставить установку на паузу для employee_phone_number?
                # проверяем, что первый символ вызываемого номера 7, меняем на 8 и делаем originate
                if data['contact_phone_number'][0] == '7':
                    number = f"8{data['contact_phone_number'][1:]}"
                    call_with_pause(operator, number)
                    return good_request_call()
                # проверяем, что первый символ вызываемого номера 8, ничего не меняем и делаем originate
                elif data['contact_phone_number'][0] == '8':
                    number = f"{data['contact_phone_number']}"
                    call_with_pause(operator, number)
                    return good_request_call()
                else:
                    return bad_request("bad outgoing full number without 7 or 8")
            else:
                return bad_request("len outgoing number not 11")
        else:
            return bad_request("len extension 6 or lower")

    elif data["method"] == 'call_records':
        attempt = 0
        local_attempt = 0
        ids = (data['call_id'], data['parent_id'])
        for id in ids:
            result = mysql_connect.call_record(mysql_connect.connection(), id)
            logs.log_write('crmconnect', id, None)
            logs.log_write('crmconnect', result, None)
            if result == 'error':
                # Если проблема с подключением к БД
                return bad_request("Mysql connection error")
            elif result == None:
                result = mysql_connect.call_record(mysql_connect.connection_local(), id)
                if result == 'error':
                    # Если проблема с подключением к БД
                    return bad_request("Mysql connection error")
                elif result == None:
                    local_attempt += 1
                    attempt += 1
                    if local_attempt == 2 or attempt == 2:
                        return bad_request("not found id")
                    else:
                        continue
                else:
                    return good_request(result)
            else:
                return good_request(result)


def call_with_pause(operator, number):
    os.system(f"asterisk -rx 'queue pause member Local/{operator}@from-queue/n queue 7200 reason call_originate'")
    logs.log_write('crmconnect', f'pause member {operator}', None)
    time.sleep(2)
    originate_ami.originate(operator, number)
    os.system(f"asterisk -rx 'queue unpause member Local/{operator}@from-queue/n queue 7200 reason call_originate'")
    logs.log_write('crmconnect', f'unpause member {operator}', None)


def good_request_call():
    response_data = {
        "error": 0,
        "data": None
    }
    logs.log_write('crmconnect', response_data, None)
    return web.json_response(response_data)


def good_request(result):
    response_data = {
        "error": 0,
        "data": {
            "file_link": result
        }
    }
    logs.log_write('crmconnect', response_data, None)
    return web.json_response(response_data)


def bad_request(reason):
    response_data = {
        "error": 1,
        "data": reason
    }
    logs.log_write('crmconnect', response_data, None)
    return web.json_response(response_data)


def web_server():
    app = web.Application()
    app.add_routes([web.route('*', '/', all_handler)])
    web.run_app(app, host='0.0.0.0', port='8081')

