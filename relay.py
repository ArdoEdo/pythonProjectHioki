def recfromrelay(r_conn):
    """
    Restituisce il messaggio a schermo e 1 se in errore o 0 con esito positivo
    :param r_conn: serial
    :return: double
    """
    msgfromRelay = bytes(range(0))
    try:
        while True:
            if r_conn.inWaiting() > 0:  # verifico dati nel buffer
                rcv = r_conn.read(1)
                if rcv == b"\n":  # break sul LF
                    msgfromRelay = msgfromRelay.decode('utf-8')
                    break
                else:
                    msgfromRelay = msgfromRelay + rcv
    except Exception as e:
        print("Errore in ricezione")
        print(e)
        return 1
    else:
        print(msgfromRelay)
        return 0


def check_relay (r_conn, msg):
    """
    Verifica la presa di configurazione del relay
    :param r_conn: serial
    :param msg: string
    :return: None
    """
    while True:
        r_conn.write(bytes(msg, 'utf-8'))
        if not recfromrelay(r_conn):
            break
