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



# Value to Hex
def ValToHex(value):

    temp = int(value*100)       # 0.01-->1

    param2 = temp % 240  # necessario per la codifica dei primi 8 bit
    param1 = temp // 240  # necessario per la codifica degli alri 8 bit

    hexencode = '{0:02X} {1:02X}'.format(param1, param2)
    #print("codifica esadecimale parametro:", hexencode)

    return hexencode


#XOR CrC
def crc_calc(hex_ampere_str, hex_voltage_str, hex_time_str, discharge_mode_hex):

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
    print(crc)

    return crc

mode = 'd-cc'

# Calc

if mode == 'd-cc':
    dsc_type = 0x01
elif mode == 'd-cp':
    dsc_type = 0x11
elif mode == 'adjust':
    dsc_type = 0x07

n_comb = 240  # numero di combinazioni

# Stringhe di connessione
connect = 'FA 05 00 00 00 00 00 00 05 F8'
stop = 'FA 02 00 00 00 00 00 00 02 F8'
disconnect = 'FA 06 00 00 00 00 00 00 06 F8' 
# conf2 = 'FA 01 00 0A 01 A1 00 00 AB F8'    # DC-CC 0.10 4.01V 0M

# init choise
choise = '0'

while choise != '6':
    print("Inserire operazione desiderata:\n 1: Connetti al dispositivo \n 2: Avvia nuova misura \n 3: Stop misura in corso\n"
      " 4: Disconnetti dal dispositivo [chiusura seriale]\n 5: Disconnessione dal dispositivo [chiusura seriale e stop misure]\n 6: Termina programma\n")

    choise = input()
    # ricerca della porta su cui è collegato l'EBC controller
    ports = serial.tools.list_ports.comports()

    if choise == '1': # Connetti al dispositivo
        print("\n Selezionare la porta COM tra quelle elencate su cui è collegato il dispotivo \n")
        for port, desc, hwid in sorted(ports):
            print("{}: {} [{}]".format(port, desc, hwid))  # stampo la lista delle COM disponibili

        print("Inserire il nome della COM: es[COM#] ")
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

    elif choise == '2':  # Invio nuova configurazione al dispositivo

            try:
                s.write(bytes.fromhex(connect))
                print("Connesso, Il dispositivo risponde: [verificare]", s.read(19))
                print("Inserire valore di corrente di scarica:")
                test_val = float(input())  # Valore di corrente di scarica
                print("Inserire valore di tensione minima:")
                cutoff_volt = float(input())
                print("Inserire valore tempo massimo di scarica:")
                max_time = float(input())  # Minuti di scarica, solo valori interi!

                print(test_val, cutoff_volt, max_time)

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
                print("configurazione inviata al dispositivo, avvio misura ... ")

            except:
                    print("Errore nell invio della configurazione, ripetere connessione al dispositivo")

    elif choise == '3': # Stop misura in corso

        try:
            print("Stop della misura in corso")
            s.write(bytes.fromhex(stop))

        except:
            print("Errore nell invio della configurazione di stop, ripetere connessione al dispositivo")

        else:
            print('Misura stoppata')

    elif choise == '4': # disconnessione dal dispositivo #[Chiusura seriale di comunicazione]

        try:
            print("Disconnessione dal dispositivo [chiusura seriale]")
            s.close()
        except:
            print("Errore nella chiusura della seriale, verificare sia aperta")

    elif choise == '5':

        try:
            print("Disconnessione dal dispositivo [chiusura seriale e stop misure]")
            s.write(bytes.fromhex(stop))
            tm.sleep(1)  # obbligatorio per intercettare entrambi i messaggi
            s.write(bytes.fromhex(disconnect))
            s.close()
        except:
            print("Errore nell'invio della configurazione di disconnect, verificare apertura seriale")

    else:
            print("Programma terminato")
            exit(0)



