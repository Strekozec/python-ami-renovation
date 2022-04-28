#!/usr/bin/python3

import events
import time
import asyncio
import json
import requests
import panoramisk
from pprint import pprint
import crm_connect
from panoramisk import Manager
from collections import defaultdict

url = 'http://192.168.129.55:3010/api/calls?api_key=2f71cb779d503188e42bdff2aeaa234c'
headers = {'Content-type': 'application/json',  # Определение типа данных
           'Content-Encoding': 'utf-8'}

all_id = defaultdict(dict)  # Словарь сбора параметров для отправки в CRM
not_use_linkedid = set()  # Множество, в которое собираем Linkedid, внутренних вызовов и вызовов с внутренних на
# внешние, при Hangup удаляется определенный Linkedid

manager = Manager(loop=asyncio.get_event_loop(),
                  host='127.0.0.1',
                  port=5038,
                  username='testfull',
                  secret='1736ffe643a4d72efa9fbce0dc50b1fc',
                  ping_delay=5,
                  )


# Функция асинхронно ловит события и каждое событие обрабатывает отдельно по условию
async def callback(mngr: panoramisk.Manager, msg: panoramisk.message) -> None:
    """Catch AMI Events/Actions"""
    # Проверяем, что подключились
    if msg.event == "FullyBooted":
        with open('/var/log/amiconnect.log', 'a') as file:
            file.write("CONNECT" + "\n" + "\n" + "\n" + "\n")
        # print("Connect")

    # Смотрим, что это новый канал
    elif msg.event == "Newchannel":
        event = {"Event": msg.event.lower(),
                 "Channel": msg.Channel,
                 "CallerIDNum": msg.CallerIDNum,
                 "Uniqueid": msg.Uniqueid,
                 "Linkedid": msg.Linkedid,
                 "ChannelState": msg.ChannelState}
        event_call = event
        log_write('event_call_log', event_call, None)
        # Проверяем, что вызов входящий, а именно, что канал образован номером, длина которого превышает 6 знаков и
        # записываем в all_id необходимые значения для дальнейшей отправки в CRM
        if msg.Linkedid == msg.Uniqueid and len(msg.CallerIDNum) > 4:
            log_write('all_id_log', all_id, None)
            all_id[msg.Linkedid]['type'] = "in"
            all_id[msg.Linkedid]['contact_phone_number'] = msg.CallerIDNum
            all_id[msg.Linkedid]['clinic_phone_number'] = f"8{msg.Exten}"
            all_id[msg.Linkedid]['exten_channel_waiting'] = dict()
            payload = events.event_call(msg.Uniqueid,
                                        all_id[msg.Linkedid]['type'],
                                        all_id[msg.Linkedid]['contact_phone_number'],
                                        all_id[msg.Linkedid]['clinic_phone_number'])
            send_request(payload, 'event_call_log')
            # all_id[msg.Linkedid]['type'], ['contact_phone_number'], ['clinic_phone_number'], ['exten_channel_waiting']

        # Проверяем, что вызов исходящий внешний, а именно, что канал образован номером, длина которого не превышает
        # 6 знаков (внутренний номер) и отправляем данные в срм.
        elif msg.Linkedid == msg.Uniqueid and len(msg.CallerIDNum) < 6 and (len(msg.Exten) > 6 or msg.Exten == 's'):
            log_write('all_id_log', all_id, None)
            # Для вызова из СРМ, где мы сами формируем Linkedid:
            if f'-{msg.CallerIDNum}-' in msg.Linkedid:
                all_id[msg.Linkedid]['type'] = "out"
                all_id[msg.Linkedid]['contact_phone_number'] = msg.Linkedid[-11:]
            # Для остальных вызовов
            else:
                all_id[msg.Linkedid]['type'] = "out"
                all_id[msg.Linkedid]['contact_phone_number'] = msg.Exten
            all_id[msg.Linkedid]['clinic_phone_number'] = None
            all_id[msg.Linkedid]['exten'] = msg.CallerIDNum
            payload = events.event_call(msg.Uniqueid,
                                        all_id[msg.Linkedid]['type'],
                                        all_id[msg.Linkedid]['contact_phone_number'],
                                        all_id[msg.Linkedid]['clinic_phone_number'])
            send_request(payload,'event_call_log')
            # all_id[msg.Linkedid]['type'], ['contact_phone_number'], ['clinic_phone_number'], ['exten']


    # Поиск совпадений для состояния Ringing у нового канала (WAITING для CRM)
    # Проверяем, что канал и Linkedid находится в множестве

    elif msg.event == 'DialBegin' and msg.Linkedid in all_id:
        event = {"Event": msg.event.lower(),
                 "Channel": msg.Channel,
                 "CallerIDNum": msg.CallerIDNum,
                 "ConnectedLineNum": msg.ConnectedLineNum,
                 "Uniqueid": msg.Uniqueid,
                 "Linkedid": msg.Linkedid,
                 "DestCallerIDNum": msg.DestCallerIDNum,
                 "ChannelState": msg.ChannelState}
        event_waiting = event
        log_write('event_waiting_log', event_waiting, None)
        # Для входящих waiting
        if msg.ChannelState == '4' and all_id[msg.Linkedid]['type'] == "in":
            if 'Local' in msg.Channel:
                all_id[msg.Linkedid]['exten_channel_waiting'][msg.Uniqueid] = msg.DestCallerIDNum
                payload = events.event_waiting(msg.Uniqueid,
                                               msg.Linkedid,
                                               all_id[msg.Linkedid]['type'],
                                               all_id[msg.Linkedid]['contact_phone_number'],
                                               all_id[msg.Linkedid]['clinic_phone_number'],
                                               all_id[msg.Linkedid]['exten_channel_waiting'][msg.Uniqueid])
                send_request(payload, 'event_waiting_log')
                # all_id[msg.Linkedid]['type'], ['contact_phone_number'], ['clinic_phone_number'], ['exten_channel_waiting'][msg.Uniqueid]
            else:
                all_id[msg.Linkedid]['exten_channel_waiting'][msg.DestUniqueid] = msg.DestCallerIDNum
                payload = events.event_waiting(msg.DestUniqueid,
                                               msg.Linkedid,
                                               all_id[msg.Linkedid]['type'],
                                               all_id[msg.Linkedid]['contact_phone_number'],
                                               all_id[msg.Linkedid]['clinic_phone_number'],
                                               all_id[msg.Linkedid]['exten_channel_waiting'][msg.DestUniqueid])
                send_request(payload, 'event_waiting_log')
                # all_id[msg.Linkedid]['type'], ['contact_phone_number'], ['clinic_phone_number'], ['exten_channel_waiting'][msg.DestUniqueid]

        # Для исходящих waiting
        elif msg.ChannelState == '4' or msg.ChannelState == '6' and all_id[msg.Linkedid]['type'] == "out":
            all_id[msg.Linkedid]['exten_id_waiting'] = msg.DestUniqueid
            all_id[msg.Linkedid]['exten_number_waiting'] = all_id[msg.Linkedid]['exten']
            payload = events.event_waiting(all_id[msg.Linkedid]['exten_id_waiting'],
                                           msg.Linkedid,
                                           all_id[msg.Linkedid]['type'],
                                           all_id[msg.Linkedid]['contact_phone_number'],
                                           all_id[msg.Linkedid]['clinic_phone_number'],
                                           all_id[msg.Linkedid]['exten'])
            send_request(payload, 'event_waiting_log')
            # all_id[msg.Linkedid]['type'], ['contact_phone_number'], ['clinic_phone_number'], ['exten'], ['exten_id_waiting'], ['exten_number_waiting']

        # Для исходящих из CRM waiting
        elif msg.ChannelState == '4' or msg.ChannelState == '6' and all_id[msg.Linkedid]['type'] == "out_from_crm":
            all_id[msg.Linkedid]['exten_id_waiting'] = msg.DestUniqueid
            all_id[msg.Linkedid]['exten_number_waiting'] = all_id[msg.Linkedid]['exten']
            payload = events.event_waiting(all_id[msg.Linkedid]['exten_id_waiting'],
                                           msg.Linkedid,
                                           all_id[msg.Linkedid]['type'],
                                           all_id[msg.Linkedid]['contact_phone_number'],
                                           all_id[msg.Linkedid]['clinic_phone_number'],
                                           all_id[msg.Linkedid]['exten'])
            send_request(payload, 'event_waiting_log')

    # Ответ на вызов UP
    # Ловим event DialEnd и проверяем, что  linkedid находится в множестве
    elif msg.event == "DialEnd" and msg.Linkedid in all_id:
        event = {"Event": msg.event.lower(),
                 "Channel": msg.Channel,
                 "CallerIDNum": msg.CallerIDNum,
                 "Uniqueid": msg.Uniqueid,
                 "Linkedid": msg.Linkedid,
                 "DestCallerIDNum": msg.DestCallerIDNum,
                 "ChannelState": msg.ChannelState}
        event_up = event
        log_write('event_up_log', event_up, None)
        # Смотрим статус канала, который завершил Dial, если Answer, то собираем данные из него
        if msg.DialStatus == 'ANSWER' and msg.ChannelState == '4' or msg.ChannelState == '6':
            # Проверяем что номер назначения не внешний, если это внутренний Local, то для id записи используем его
            if all_id[msg.Linkedid]['type'] == "in":
                if 'Local' in msg.Channel and \
                        msg.Uniqueid in all_id[msg.Linkedid]['exten_channel_waiting']:
                    all_id[msg.Linkedid]['exten_uniqueid_up'] = msg.Uniqueid
                    all_id[msg.Linkedid]['exten_number_up'] = msg.DestCallerIDNum
                    all_id[msg.Linkedid]['exten_channel_up'] = "Local"
                    payload = events.event_up(all_id[msg.Linkedid]['exten_uniqueid_up'], all_id[msg.Linkedid]['exten_number_up'])
                    send_request(payload, 'event_up_log')
                    del all_id[msg.Linkedid]['exten_channel_waiting'][msg.Uniqueid]
                    # all_id[msg.Linkedid]['type'], ['contact_phone_number'], ['clinic_phone_number'], ['exten_channel_waiting'], ['exten_uniqueid_up'], ['exten_number_up'], ['exten_channel_up']
                elif 'SIP' in msg.Channel and \
                        msg.DestUniqueid in all_id[msg.Linkedid]['exten_channel_waiting']:
                    all_id[msg.Linkedid]['exten_uniqueid_up'] = msg.DestUniqueid
                    all_id[msg.Linkedid]['exten_number_up'] = msg.DestCallerIDNum
                    all_id[msg.Linkedid]['exten_channel_up'] = "SIP"
                    payload = events.event_up(all_id[msg.Linkedid]['exten_uniqueid_up'], all_id[msg.Linkedid]['exten_number_up'])
                    send_request(payload, 'event_up_log')
                    del all_id[msg.Linkedid]['exten_channel_waiting'][msg.DestUniqueid]
                    # all_id[msg.Linkedid]['type'], ['contact_phone_number'], ['clinic_phone_number'], ['exten_channel_waiting'], ['exten_uniqueid_up'], ['exten_number_up'], ['exten_channel_up']
            # Для исходящего на внешнее направление
            elif all_id[msg.Linkedid]['type'] == "out":
                all_id[msg.Linkedid]['exten_uniqueid_up'] = all_id[msg.Linkedid]['exten_id_waiting']
                all_id[msg.Linkedid]['exten_number_up'] = all_id[msg.Linkedid]['exten_number_waiting']
                payload = events.event_up(all_id[msg.Linkedid]['exten_uniqueid_up'],
                                          all_id[msg.Linkedid]['exten_number_waiting'])
                send_request(payload, 'event_up_log')
                del all_id[msg.Linkedid]['exten_id_waiting']
                del all_id[msg.Linkedid]['exten_number_waiting']
                # all_id[msg.Linkedid]['type'], ['contact_phone_number'], ['clinic_phone_number'], ['exten'], ['exten_uniqueid_up'], ['exten_number_up']


    # Завершение вызова
    elif msg.event == "Hangup":
        event = {"Event": msg.event.lower(),
                 "Channel": msg.Channel,
                 "CallerIDNum": msg.CallerIDNum,
                 "ConnectedLineNum": msg.ConnectedLineNum,
                 "Uniqueid": msg.Uniqueid,
                 "Linkedid": msg.Linkedid,
                 "ChannelState": msg.ChannelState}
        event_hangup = event
        log_write('event_hangup_log', event_hangup, None)
        # pprint(event)
        # print('')
        # Для удаления данных о звонке из all_id проверяем, что linkedid и uniqueid равны
        # Основной внешний канал
        if msg.Linkedid in all_id and msg.Linkedid == msg.Uniqueid and msg.Linkedid not in not_use_linkedid:
            # Проверяем, что exten_uniqueid_up есть в словаре, значит Hangup основного канала прилетел раньше,
            # поэтому нам необходимо сначала отправить hangup внутреннего, а затем внешнего
            # ОСНОВНОЙ ВНЕШНИЙ. Если внутренний ответил на звонок
            if 'exten_uniqueid_up' in all_id[msg.Linkedid]:
                payload = events.event_hangup(all_id[msg.Linkedid]['exten_uniqueid_up'],
                                              all_id[msg.Linkedid]['exten_number_up'])
                send_request(payload, 'event_hangup_log')
                payload = events.event_hangup(msg.Linkedid,
                                              all_id[msg.Linkedid]['contact_phone_number'])
                send_request(payload, 'event_hangup_log')
                del all_id[msg.Linkedid]
            # Проверка hangup для тех, кто был в состоянии waiting
            elif 'exten_channel_waiting' in all_id[msg.Linkedid] and \
                    bool(all_id[msg.Linkedid]['exten_channel_waiting']) == True:
                for id in all_id[msg.Linkedid]['exten_channel_waiting']:
                    payload = events.event_hangup(id,
                                                  all_id[msg.Linkedid]['exten_channel_waiting'][id])
                    send_request(payload, 'event_hangup_log')

                payload = events.event_hangup(msg.Linkedid,
                                              all_id[msg.Linkedid]['contact_phone_number'])
                send_request(payload, 'event_hangup_log')
                del all_id[msg.Linkedid]
            # Hangup основного канала, если он не был завершен до внутреннего
            else:
                if all_id[msg.Linkedid]['type'] == 'in':
                    # Hangup внешнего после того, как завершили exten_uniqueid_up
                    payload = events.event_hangup(msg.Linkedid,
                                                  all_id[msg.Linkedid]['contact_phone_number'])
                    send_request(payload, 'event_hangup_log')
                    del all_id[msg.Linkedid]
                elif all_id[msg.Linkedid]['type'] == 'out':
                    # Hangup внешнего после того, как завершили exten_uniqueid_up
                    payload = events.event_hangup(msg.Linkedid,
                                                  all_id[msg.Linkedid]['contact_phone_number'])
                    send_request(payload, 'event_hangup_log')
                    del all_id[msg.Linkedid]

        # Не основной внешний канал
        elif msg.Linkedid in all_id and msg.Linkedid != msg.Uniqueid:
            # Hangup для внутреннего, который ответил на вызов
            if 'exten_uniqueid_up' in all_id[msg.Linkedid] \
                    and all_id[msg.Linkedid]['exten_uniqueid_up'] == msg.Uniqueid:
                payload = events.event_hangup(all_id[msg.Linkedid]['exten_uniqueid_up'],
                                              all_id[msg.Linkedid]['exten_number_up'])
                send_request(payload, 'event_hangup_log')
                del all_id[msg.Linkedid]['exten_uniqueid_up']
                del all_id[msg.Linkedid]['exten_number_up']
                '''# Удаление данных о Hangup для внутреннего, который был завершен в основном канале
                elif 'exten_uniqueid_up_hangup' in all_id[msg.Linkedid] \
                    and all_id[msg.Linkedid]['exten_uniqueid_up_hangup'] == msg.Uniqueid:
                del all_id[msg.Linkedid]['exten_uniqueid_up_hangup']'''
            # Hangup внутренних, которые были waiting
            # Входящие звонки
            elif 'exten_channel_waiting' in all_id[msg.Linkedid] and \
                    msg.Uniqueid in all_id[msg.Linkedid]['exten_channel_waiting']:
                # pprint(all_id)
                payload = events.event_hangup(msg.Uniqueid,
                                              all_id[msg.Linkedid]['exten_channel_waiting'][msg.Uniqueid])
                send_request(payload, 'event_hangup_log')
                del all_id[msg.Linkedid]['exten_channel_waiting'][msg.Uniqueid]
            # Исходящие звонки
            elif 'exten_id_waiting' in all_id[msg.Linkedid] and \
                    all_id[msg.Linkedid]['exten_id_waiting'] == msg.Uniqueid:
                payload = events.event_hangup(msg.Uniqueid,
                                              all_id[msg.Linkedid]['contact_phone_number'])
                send_request(payload, 'event_hangup_log')
                del all_id[msg.Linkedid]['exten_id_waiting']


        # Проверяем, что linkedid и uniqueid равны, и что linkedid приндлежит множеству и удалем его из множества
        elif msg.Linkedid == msg.Uniqueid and msg.Linkedid in not_use_linkedid:
            not_use_linkedid.discard(msg.Linkedid)

    # Постановка вызова на удержание и Снятие вызова с удержания
    elif msg.event == "Hold" or msg.event == "Unhold":
        if msg.event == "Hold" and msg.Linkedid not in not_use_linkedid:
            payload = events.event_hold(msg.Uniqueid, "on")
            send_request(payload, 'send_hold')
        elif msg.event == "Unhold" and msg.Linkedid not in not_use_linkedid:
            payload = events.event_hold(msg.Uniqueid, "off")
            send_request(payload, 'send_unhold')


# Функия отправки запроса в систему CRM
def send_request(payload, event):
    comment = 'send_' + str(event)
    answer = (requests.post(url, data=json.dumps(payload), headers=headers)).json()
    log_write(comment, payload, answer)


# Запись в лог файл для дебага
def log_write(comment, payload, answer):
    nowtime = time.strftime('%H:%M:%S')
    # pprint(nowtime + '' + str(payload))
    with open('/var/log/renovation/amiconnect.log', 'a') as file:
        file.write(comment + "   " + nowtime + " " + str(payload) + "\n")
        file.write(str(answer) + "\n")


def main(mngr: panoramisk.Manager) -> None:
    mngr.register_event('*', callback=callback)
    mngr.connect()
    try:
        mngr.loop.run_forever(crm_connect.web_server())
    except (SystemExit, KeyboardInterrupt):
        mngr.loop.close()
        exit(0)


if __name__ == '__main__':
    main(manager)
