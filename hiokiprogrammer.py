import time
import pandas as pd
import serial


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
            print("Query inviata")
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

# INPUT
port = 'COM5'
baudrate = 9600
conf_path = "conf/conf.txt"
dest_path = "meas/meas.csv"
freq_vect = [1000, 800, 700, 500]

# CALC
s = serial.Serial(port, baudrate=9600, timeout=0)

# Lettura configurazione Hioki
with open(conf_path) as f:
    for line in f:
        line = line.partition('#')[0] # opzionale ?
        command = line.strip()
        print(command)
        sendtohioki(s, command)


meas_list = [] # contenitore delle stringhe con i risultati di misura e relativa frequenza di acquisizione

for x in freq_vect:
    command = ":FREQ "+str(x)
    sendtohioki(s, command)
    print("ho inviato la frequenza " + str(x))
    sendtohioki(s, ":FREQ?") # chiedo di mostrare la frequenza impostata
    print("avvio la misura:")
    meas_list.append(sendtohioki(s, "READ?")+','+"{:.5E}".format(x)) # costruisco stringa con risultato di misura più frequenza

meas_dataframe = pd.DataFrame(columns=['Data'], data=meas_list)


meas_dataframe[['R', 'X', 'V', 'F']] = meas_dataframe.Data.str.split(",", expand=True)
meas_dataframe = meas_dataframe.drop(columns=['Data'])
print(meas_dataframe.head())
meas_dataframe.to_csv(dest_path)



