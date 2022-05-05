import time


def log_write(comment, payload, answer):
    nowtime = time.strftime("%m.%d.%Y, %H:%M:%S")
    if comment == 'originate':
        with open('/var/log/renovation/originate.log', 'a') as file:
            file.write(nowtime + " " + str(payload) + "\n")
    elif comment == 'crmconnect':
        with open('/var/log/renovation/crmconnect.log', 'a') as file:
            file.write(nowtime + " " + str(payload) + "\n")
    else:
        with open('/var/log/renovation/amiconnect.log', 'a') as file:
            file.write(comment + "   " + nowtime + " " + str(payload) + "\n")
            file.write(str(answer) + "\n")
