# Формирование payload из событий для отправки в CRM
def event_call(id, type, contact_phone_number, clinic_phone_number):
    """
                event:call
                id:Идентификатор звонка
                type:Направление звонка (in)
                contact_phone_number:Номер абонента
                clinic_phone_number:Номер клиники
    """

    payload = {"event": "call",
               "id": id,
               "type": type,
               "contact_phone_number": contact_phone_number,
               "clinic_phone_number": clinic_phone_number,
               }
    return payload


def event_waiting(id, parent_id, type, contact_phone_number, clinic_phone_number, employee_phone_number):
    """
                event:waiting
                id:Идентификатор звонка
                parent_id:Идентификатор родительского звонка (из call)
                type:Направление звонка (in)
                contact_phone_number:Номер абонента
                clinic_phone_number:8612126654
                employee_phone_number:Добавочный сотрудника
    """

    payload = {"event": "waiting",
               "id": id,
               "parent_id": parent_id,
               "type": type,
               "contact_phone_number": contact_phone_number,
               "clinic_phone_number": clinic_phone_number,
               "employee_phone_number": employee_phone_number,
               }
    return payload


def event_up(id, employee_phone_number):
    """
                event:up
                id:Идентификатор звонка
                employee_phone_number:Добавочный сотрудника
    """

    payload = {"event": "up",
               "id": id,
               "employee_phone_number": employee_phone_number,
               }
    return payload


def event_hangup(id, employee_phone_number):
    """
                event:hangup
                id:Идентификатор звонка
                employee_phone_number:Добавочный сотрудника
    """

    payload = {"event": "hangup",
               "id": id,
               "employee_phone_number": employee_phone_number,
               }
    return payload


def event_hold(id, status):
    """
                event:hold
                id:Идентификатор звонка
                status:on/off
    """

    payload = {"event": "hold",
               "id": id,
               "status": status,
               }
    return payload
