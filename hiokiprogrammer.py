import pandas as pd
def sendtohioki(ser, strMsg):
    ans_msg = ""
    try:
        strMsg = strMsg + '\r\n'  # Add a terminator, CR+LF, to transmitted command
        ser.write(bytes(strMsg, 'utf-8'))  # Convert to byte type and send
    except Exception as e:
            print("Error while sending")
            ans_msg = "Error"
            print(e)
    else:
        if '?' in strMsg:
            print("Query riceived")
            ans_msg = recfromhioki(ser)
        else:
            print("Configuration sent")

    return ans_msg


def recfromhioki(ser):
        msgBuf = bytes(range(0))
        try:
            while True:
                if ser.inWaiting() > 0:
                    rcv = ser.read(1)
                    if rcv == b"\n":  # break sul LF
                        msgBuf = msgBuf.decode('utf-8')
                        break
                    elif rcv == b"\r":
                        pass
                    else:
                        msgBuf = msgBuf + rcv
        except Exception as e:
                print("Error while riceiving")
                print(e)
                msgBuf = "Error"

        return msgBuf


def read_conf(s, config_path):
    with open(config_path) as f:
        for line in f:
            command = line.partition('#')[0] # considera solo la parte prima dell # come comando
            print("sending the command: ", command)
            sendtohioki(s, command)
            if '#' in line:
                check = line.partition('#')[2]
            else:
                check = (command.partition(' ')[0] +'?')

            print("sending configuration check")
            print(sendtohioki(s, check))


def start_EIS(s, freq_vect, meas_list):

    for x in range(len(freq_vect)):
        command = ":FREQ "+str(freq_vect[x])
        sendtohioki(s, command)
        print("the frequency sent is " + str(freq_vect[x]))
        set_freq = sendtohioki(s, ":FREQ?")     # Query the frequency
        print("Hioki set the frequency: ", set_freq)
        freq_vect[x] = float(set_freq)
        print("Starting the measurement:")
        meas_list.append(sendtohioki(s, "READ?")+','+"{:.5E}".format(freq_vect[x]))
