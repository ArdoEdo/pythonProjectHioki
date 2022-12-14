import pandas as pd
def sendtohioki(ser, strMsg):
    ans_msg = ""
    try:
        strMsg = strMsg + '\r\n'  # Add a terminator, CR+LF, to transmitted command
        ser.write(bytes(strMsg, 'utf-8'))  # Convert to byte type and send
    except Exception as e:
            print("Errore nell'invio")
            ans_msg = "Errore"
            print(e)
    else:
        if '?' in strMsg:
            print("Query ricevuta")
            ans_msg = recfromhioki(ser)
        else:
            print("Configurazione inviata")

    return ans_msg


def recfromhioki(ser):

        msgBuf = bytes(range(0)) # Received Data

        try:
            while True:
                if ser.inWaiting() > 0:  # verifico dati nel buffer
                    rcv = ser.read(1)
                    if rcv == b"\n":  # break sul LF
                        msgBuf = msgBuf.decode('utf-8')
                        break
                    elif rcv == b"\r":  # Ignore the terminator CR
                        pass
                    else:
                        msgBuf = msgBuf + rcv
        except Exception as e:
                print("Errore in ricezione")
                print(e)
                msgBuf = "Errore"

        #print("l'hioki risponde:", msgBuf)
        return msgBuf


def read_conf(s, config_path):

# Lettura configurazione Hioki
    with open(config_path) as f:
        for line in f:
            command = line.partition('#')[0] # considera solo la parte prima dell # come comando
            print("Sto inviando allo Hioki il comando: ", command)
            sendtohioki(s, command)
            if '#' in line:
                check = line.partition('#')[2]
            else:
                check = (command.partition(' ')[0] +'?')

            print("invio verifica configurazione")
            print(sendtohioki(s, check))


def start_EIS(s, freq_vect, meas_list):

    for x in range(len(freq_vect)):
        command = ":FREQ "+str(freq_vect[x])
        sendtohioki(s, command)
        print("ho inviato la frequenza " + str(freq_vect[x]))
        set_freq = sendtohioki(s, ":FREQ?")     # chiedo di mostrare la frequenza impostata
        print("Hioki ha impostato la frequenza: ", set_freq)
        freq_vect[x] = float(set_freq)          #  sovrascrivo con il valore impostato dallo hioki
        print("avvio la misura:")
        meas_list.append(sendtohioki(s, "READ?")+','+"{:.5E}".format(freq_vect[x])) # costruisco stringa con risultato di misura più frequenza
