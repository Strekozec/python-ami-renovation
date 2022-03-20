#!/usr/bin/python3

from asterisk.ami import AMIClient
from asterisk.ami import SimpleAction
import time

def originate(operator, number):
    client = AMIClient(address='127.0.0.1',port=5038)
    client.login(username='testfull',secret='1736ffe643a4d72efa9fbce0dc50b1fc')
    action = SimpleAction(
        'Originate',
        Channel=f'SIP/{operator}',
        Exten=f'{number}',
        Priority=1,
        Context='from-internal',
        ChannelId=f'{time.time()}-{operator}-{number}',
    )
    client.send_action(action)
    client.logoff()
    log_write(payload=f'{operator}-{number}')
    return


def log_write(payload):
    nowtime = time.strftime('%H:%M:%S')
    with open('/var/log/renovation/originate.log', 'a') as file:
        file.write(time.strftime("%m.%d.%Y, %H:%M:%S") + " " + str(payload) + "\n")

