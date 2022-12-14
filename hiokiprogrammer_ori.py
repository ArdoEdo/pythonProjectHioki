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

# INPUT
port = 'COM5'
baudrate = 9600
conf_path = "conf/conf.txt"
dest_path = "meas/meas.csv"
freq_vect = [1000, 800, 700, 500, 1.1]


# CALC
s = serial.Serial(port, baudrate=9600, timeout=0)

# Lettura configurazione Hioki
with open(conf_path) as f:
    for line in f:
        command = line.partition('#')[0] # considera solo la parte prima dell # come comando
        #command = line.strip()
        print("Sto inviando allo Hioki il comando: ", command)
        sendtohioki(s, command)
        if '#' in line:
            check = line.partition('#')[2]
        else:
            check = (command.partition(' ')[0] +'?')

        print("invio verifica configurazione")
        print(sendtohioki(s, check))


meas_list = [] # contenitore delle stringhe con i risultati di misura e relativa frequenza di acquisizione


for x in range(len(freq_vect)):
    command = ":FREQ "+str(freq_vect[x])
    sendtohioki(s, command)
    print("ho inviato la frequenza " + str(freq_vect[x]))
    set_freq = sendtohioki(s, ":FREQ?")     # chiedo di mostrare la frequenza impostata
    print("Hioki ha impostato la frequenza: ", set_freq)
    freq_vect[x] = float(set_freq)          #  sovrascrivo con il valore impostato dallo hioki
    print("avvio la misura:")
    meas_list.append(sendtohioki(s, "READ?")+','+"{:.5E}".format(freq_vect[x])) # costruisco stringa con risultato di misura più frequenza

meas_dataframe = pd.DataFrame(columns=['Data'], data=meas_list)
#print("Stampo le frequenze impostate dallo hioki:", freq_vect)


meas_dataframe[['R', 'X', 'V', 'F']] = meas_dataframe.Data.str.split(",", expand=True)
meas_dataframe = meas_dataframe.drop(columns=['Data'])
print(meas_dataframe.head())
meas_dataframe.to_csv(dest_path)



