"""Script per la codifica in esadecimale di valori di Tensione, Corrente, Tempo di Scarica...
per programmare il dispositivo ZKE |nome dispositivo|

Fasi comunicazione:
1. Richiesta di connessione al dispositivo con Connect
2. Risposta del dispositivo con ANS Device
3. Passaggio stringa di start con configurazione per avviare le misure
...


COMMUNICATION STRING
Connect = FA 05 00 00 00 00 00 00 05 F8                 # Connessione al dispositivo
Stop = FA 02 00 00 00 00 00 00 02 F8                    # Stop misure
Disconnect = FA 06 00 00 00 00 00 00 06 F8              # Disconnessione dal dispositivo
Start = FA xx xx xx xx xx xx xx xx F8                   # lo start invia l'intera configurazione di misura
Adjust = FA 07 xx xx xx xx xx xx xx F8                  # aggiorna la configurazione di misura con i nuovi valori inseriti

Pulsanti non codificati:
Serial monitor ??
Continue ??

ANS Device : FA 00 00 00 00 00 00 00 00 00 00 0C 00 C8 00 0F 13 D8 F8

"""

import serial.tools.list_ports
import time as tm
from datetime import datetime, timedelta


# Value to Hex
def ValToHex(value):
    """
    Converte il valore ricevuto in ingresso in stringa esadecimake
    :param value: valore float da codificare
    :return: stringa esadecimale
    """

    n_comb = 240
    temp = int(value*100)       # 0.01-->1

    param2 = temp % n_comb  # necessario per la codifica dei primi 8 bit
    param1 = temp // n_comb  # necessario per la codifica degli alri 8 bit

    hexencode = '{0:02X} {1:02X}'.format(param1, param2)
    #print("codifica esadecimale parametro:", hexencode)

    return hexencode


#XOR CrC
def crc_calc(hex_ampere_str, hex_voltage_str, hex_time_str, discharge_mode_hex):
    """
    Calcola CRC con la XOR
    :param hex_ampere_str: stringa esadecimale della corrente di scarica codificata
    :param hex_voltage_str: stringa esadecimale della tensione di cutoff codificata
    :param hex_time_str: stringa esadecimale del tempo massimo di scarica codificata
    :param discharge_mode_hex: stringa esadecimale della modalita di scarica
    :return: stringa contenente CRC
    """
    n_comb = 240

    func1 = lambda hex_str: int('0x'+(hex_str.split(' ', 1))[0], 16)
    func2 = lambda hex_str: int('0x'+(hex_str.split(' ', 1))[1], 16)

    pl = [func1(hex_ampere_str), func2(hex_ampere_str), func1(hex_voltage_str), func2(hex_voltage_str),
          func1(hex_time_str), func2(hex_time_str), discharge_mode_hex]

    #print(pl)
    result = 0x0

    for k in range(0, len(pl)):
        result = result ^ pl[k]

    if result >= n_comb:
        result = result % n_comb

    crc = '{:02X}'.format(result)

    return crc

mode = 'd-cc'

# Calc

if mode == 'd-cc':
    dsc_type = 0x01
elif mode == 'd-cp':
    dsc_type = 0x11
elif mode == 'adjust':
    dsc_type = 0x07

# Stringhe di connessione
connect = 'FA 05 00 00 00 00 00 00 05 F8'
stop = 'FA 02 00 00 00 00 00 00 02 F8'
disconnect = 'FA 06 00 00 00 00 00 00 06 F8'
# conf2 = 'FA 01 00 0A 01 A1 00 00 AB F8'    # DC-CC 0.10 4.01V 0M

def zke_conn():
    """
    Apertura canale di comunicazione con dispositivo ZKE
    :return: seriale
    """
    print("\n Selezionare la porta COM tra quelle elencate su cui è collegato il dispotivo ZKE\n")
    # ricerca della porta su cui è collegato l'EBC controller
    ports = serial.tools.list_ports.comports()

    for port, desc, hwid in sorted(ports):
        print("{}: {} [{}]".format(port, desc, hwid))  # stampo la lista delle COM disponibili

    print("Inserire il nome della COM: es COM# ")
    com_port_name = input()

    # Gestione connessione
    try:
        s = serial.Serial(port='\\\\.\\' + com_port_name, baudrate=9600, parity=serial.PARITY_ODD,
                          stopbits=serial.STOPBITS_ONE,
                          bytesize=serial.EIGHTBITS, write_timeout=0, timeout=5)
    except:
        print("impossibile creare la seriale sulla COM inserita verificare se già aperta!")
        print("Programma terminato")
        exit(0)
    else:
        print("Connessione stabilita!, connesso alla porta seriale: " + com_port_name)
        print("\nTentativo di connessione con il dispositivo")

        s.write(bytes.fromhex(connect))
        return s


def new_conf(s, dsc_curr, min_volt, dsc_time):  # Invio nuova configurazione al dispositivo ZKE
      """
      Calcolo e avvio nuova scarica con la configurazione dei valori passata come parametro
      :param s: connessione seriale
      :param dsc_curr: valore corrente di scarica
      :param min_volt: valore tensione di cut off
      :param dsc_time: valore tempo di scarica
      :return: None
      """
      try:
        t_ref = datetime.now()
        t_delta = timedelta(minutes=dsc_time)
        print("Ora inizio della scarica", t_ref)
        t_sim = t_ref + t_delta
        print("Ora ipotetica fine della scarica", t_sim)
        s.write(bytes.fromhex(connect))
        #tm.sleep(5)
        print("Connesso, Il dispositivo risponde: ", bytes.hex(s.read(19), ' '))
        print("Valore di corrente di scarica:")
        test_val = dsc_curr  # Valore di corrente di scarica
        print(test_val)
        print("Valore di tensione minima:")
        cutoff_volt = min_volt
        print(cutoff_volt)
        print("Valore tempo massimo di scarica:")
        max_time = dsc_time  # Minuti di scarica, solo valori interi!
        print(max_time)

        # codifico i valori

        hex_ampere_val = ValToHex(test_val)
        hex_voltage_val = ValToHex(cutoff_volt)
        hex_time_val = ValToHex(round(max_time) / 100)
        dsc_type = 0x01
        crc = crc_calc(hex_ampere_val, hex_voltage_val, hex_time_val, dsc_type)

        # Costruisco il messaggio
        # formato--> "FA dsc_type ampere volt time crc F8"
        stx = 'FA'
        etx = 'F8'
        crc_out = crc
        volt = str(hex_voltage_val)
        ampere = str(hex_ampere_val)
        time = str(hex_time_val)
        dsc_type = '{:02X}'.format(dsc_type)

        msg_tosend = stx + ' ' + dsc_type + ' ' + ampere + ' ' + volt + ' ' + time + ' ' + crc + ' ' + etx
        print("Stampo messaggio da inviare codificato ", msg_tosend)
        s.write(bytes.fromhex(stop))
        s.write(bytes.fromhex(msg_tosend))
        print("configurazione inviata al dispositivo, avvio scarica ... ")
        tm.sleep(1)
        s.flushInput()
        print("Scarica in corso, Il dispositivo risponde:", bytes.hex(s.read(19), ' '))
        s.flushInput()
        ans_string = bytes.hex(s.read(19), ' ')
        counter = 0 #contatore check per verifica della corrente nulla

# ans_string.find("00 00", 6, 11) == -1:
        while t_sim >= datetime.now():
            if ans_string.find("fa 00 00 00") != -1 and counter < 3:  # la corrente va a 0 prima del tempo
                s.flushInput()  # svuoto il buffer
                ans_string = bytes.hex(s.read(19), ' ')
                print(ans_string)
                counter += 1
            elif ans_string.find("fa 00 00 00") == -1:     # la corrente è diversa da 0 quindi la scarica è in corso
                s.flushInput() # svuoto il buffer
                ans_string = bytes.hex(s.read(19), ' ')
                print(ans_string)
            else:
                s.flushInput() #svuoto il buffer
                print("la scarica è terminata inaspettatamente prima del tempo di scarica previsto,"
                      "tempo previsto per la fine della scarica e tempo corrente:", t_sim, t_ref)
                break


        # check azzeramento corrente di scarica
        iter = 0
        while iter <= 3:
            s.flushInput()  # svuoto il buffer
            ans_string = bytes.hex(s.read(19), ' ')
            print(ans_string)
            if ans_string.find("fa 00 00 00") != -1:
                print("Scarica completata")
                break
            else:
                print("E' stata rilevata una corrente di scarica dicversa da zero")
                iter += 1
                print("Continuo la verifica ")

        if iter == 3:
            print("Invio messaggio di stop al carico")
            s.write(bytes.fromhex(stop))


      except:
            print("Errore nell invio della configurazione, ripetere connessione al dispositivo")


def stop_meas(s): # Stop misura in corso
    """
    Stop misura in corso
    :param s: connessione seriale
    :return: None
    """
    try:
        print("Stop della misura in corso")
        s.write(bytes.fromhex(stop))

    except:
        print("Errore nell invio della configurazione di stop, ripetere connessione al dispositivo")

    else:
        print('Misura stoppata')


def disconnectserial_zke(s): # disconnessione dal dispositivo #[Chiusura seriale di comunicazione]
    """
    Disconnessione dal dispositivo chiudendo la seriale
    :param s: connessione seriale
    :return: None
    """
    try:
        print("Disconnessione dal dispositivo [chiusura seriale]")
        s.close()
    except:
        print("Errore nella chiusura della seriale, verificare sia aperta")


def disconnectserial_andstop(s):
    """
    Arresto della misura e disconnessione seriale dal dispositivo
    :param s: connessione seriale
    :return: None
    """
    try:
        print("Disconnessione dal dispositivo [chiusura seriale e stop misure]")
        s.write(bytes.fromhex(stop))
        tm.sleep(1)  # obbligatorio per intercettare entrambi i messaggi
        s.write(bytes.fromhex(disconnect))
        s.close()
    except:
        print("Errore nell'invio della configurazione di disconnect, verificare apertura seriale")




