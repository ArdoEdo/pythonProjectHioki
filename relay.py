def recfromrelay(r_conn):
    """
    Returns the on-screen message and 1 if in error or 0 with positive result
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
        print("error on communication channel")
        print(e)
        return 1
    else:
        print(msgfromRelay)
        return 0


def check_relay (r_conn, msg):
    """
    Verify that the relay has taken the configuration
    :param r_conn: serial
    :param msg: string
    :return: None
    """
    while True:
        r_conn.write(bytes(msg, 'utf-8'))
        if not recfromrelay(r_conn):
            break
