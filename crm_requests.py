import requests
import logs
import json

retry_count = 5
timeout = 1
url = 'http://192.168.129.55:3010/api/calls?api_key=2f71cb779d503188e42bdff2aeaa234c'
headers = {'Content-type': 'application/json',  # Определение типа данных
           'Content-Encoding': 'utf-8'}


# Функия отправки запроса в систему CRM
def send_request(payload, event):
    for i in range(retry_count):
        try:
            comment = 'send_' + str(event)
            answer = (requests.post(url, data=json.dumps(payload), headers=headers)).json()
            logs.log_write(comment, payload, answer)
            break
        except:
            comment = 'except' + str(event)
            answer = ''
            logs.log_write(comment, payload, answer)
