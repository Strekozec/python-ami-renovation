#!/usr/bin/python3

from asterisk.ami import AMIClient
from asterisk.ami import SimpleAction
import time
import logs

def originate(operator, number):
    client = AMIClient(address='127.0.0.1', port=5038)
    client.login(username='testfull', secret='1736ffe643a4d72efa9fbce0dc50b1fc')
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
    logs.log_write('originate', f'{operator}-{number}', None)
    return

