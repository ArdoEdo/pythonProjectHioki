"""
COMMUNICATION STRINGs
Connect = FA 05 00 00 00 00 00 00 05 F8
Stop = FA 02 00 00 00 00 00 00 02 F8
Disconnect = FA 06 00 00 00 00 00 00 06 F8
Start = FA xx xx xx xx xx xx xx xx F8
Adjust = FA 07 xx xx xx xx xx xx xx F8

Buttons not encoded:
Serial monitor
Continue

Typical answer message
ANS Device : FA xx xx xx xx xx xx xx xx xx xx xx xx xx xx xx xx xx F8

"""

import serial.tools.list_ports
import time as tm
from datetime import datetime, timedelta


# Value to Hex
def ValToHex(value):
    """
    Conversion from double to Hex
    :param value: value to encode
    :return: Hex string
    """

    n_comb = 240
    temp = int(value*100)       # 0.01-->1

    param2 = temp % n_comb  # to encode first 8 bit
    param1 = temp // n_comb  # to encode the next 8 bit

    hexencode = '{0:02X} {1:02X}'.format(param1, param2)

    return hexencode


#XOR CrC
def crc_calc(hex_ampere_str, hex_voltage_str, hex_time_str, discharge_mode_hex):
    """
    Crc calcutator with Xor method
    :param hex_ampere_str: Hex string of current encoded
    :param hex_voltage_str: Hex string of cutOff voltage encoded
    :param hex_time_str: Hex string of max time encoded
    :param discharge_mode_hex: Hex string of discarge mode
    :return: string
    """
    n_comb = 240

    func1 = lambda hex_str: int('0x'+(hex_str.split(' ', 1))[0], 16)
    func2 = lambda hex_str: int('0x'+(hex_str.split(' ', 1))[1], 16)

    pl = [func1(hex_ampere_str), func2(hex_ampere_str), func1(hex_voltage_str), func2(hex_voltage_str),
          func1(hex_time_str), func2(hex_time_str), discharge_mode_hex]

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

connect = 'FA 05 00 00 00 00 00 00 05 F8'
stop = 'FA 02 00 00 00 00 00 00 02 F8'
disconnect = 'FA 06 00 00 00 00 00 00 06 F8'


def zke_conn():
    """
    Open serial communication channel with ZKE
    :return: serial
    """
    print("Avaiable serial ports, select connection with Active Load (ZKE):")
    ports = serial.tools.list_ports.comports()

    for port, desc, hwid in sorted(ports):
        print("{}: {} [{}]".format(port, desc, hwid))

    print("Enter COM name: es COM# ")
    com_port_name = input()

    try:
        s = serial.Serial(port='\\\\.\\' + com_port_name, baudrate=9600, parity=serial.PARITY_ODD,
                          stopbits=serial.STOPBITS_ONE,
                          bytesize=serial.EIGHTBITS, write_timeout=0, timeout=5)
    except:
        print("Unable to open the serial communication on the given COM, check if already open!")
        print("Program ended")
        exit(0)
    else:
        print("Connection established! Connected to the serial port: " + com_port_name)
        print("\nConnecting with the device")

        s.write(bytes.fromhex(connect))
        return s


def new_conf(s, dsc_curr, min_volt, dsc_time):
      """
      Calculate and send new configuration to the Load (ZKE)
      :param s: serial
      :param dsc_curr: current value
      :param min_volt: cutOff value
      :param dsc_time: discharge time value
      :return: None
      """
      try:
        t_ref = datetime.now()
        t_delta = timedelta(minutes=dsc_time)
        print("Discharge start time", t_ref)
        t_sim = t_ref + t_delta
        print("Expected end time of discharge", t_sim)
        s.write(bytes.fromhex(connect))
        print("Connected, the device reply: ", bytes.hex(s.read(19), ' '))
        print("Discharge current value:")
        test_val = dsc_curr  # Valore di corrente di scarica
        print(test_val)
        print("Minimum voltage value:")
        cutoff_volt = min_volt
        print(cutoff_volt)
        print("Maximum discharge time value:")
        max_time = dsc_time
        print(max_time)

        # encode

        hex_ampere_val = ValToHex(test_val)
        hex_voltage_val = ValToHex(cutoff_volt)
        hex_time_val = ValToHex(round(max_time) / 100)
        dsc_type = 0x01
        crc = crc_calc(hex_ampere_val, hex_voltage_val, hex_time_val, dsc_type)

        # Build the message
        # format--> "FA dsc_type ampere volt time crc F8"
        stx = 'FA'
        etx = 'F8'
        crc_out = crc
        volt = str(hex_voltage_val)
        ampere = str(hex_ampere_val)
        time = str(hex_time_val)
        dsc_type = '{:02X}'.format(dsc_type)

        msg_tosend = stx + ' ' + dsc_type + ' ' + ampere + ' ' + volt + ' ' + time + ' ' + crc + ' ' + etx
        print("Print encoded message to send ", msg_tosend)
        s.write(bytes.fromhex(stop))
        s.write(bytes.fromhex(msg_tosend))
        print("configuration sent to the device, discharge startup ... ")
        tm.sleep(1)
        s.flushInput()
        print("discharge in progress, the device reply:", bytes.hex(s.read(19), ' '))
        s.flushInput()
        ans_string = bytes.hex(s.read(19), ' ')
        counter = 0

        while t_sim >= datetime.now():
            if ans_string.find("fa 00 00 00") != -1 and counter < 3:  # current go to 0 before estimated time
                s.flushInput()  # svuoto il buffer
                ans_string = bytes.hex(s.read(19), ' ')
                print(ans_string)
                counter += 1
            elif ans_string.find("fa 00 00 00") == -1:     # current differs from zero, discharge in progress
                s.flushInput()
                ans_string = bytes.hex(s.read(19), ' ')
                print(ans_string)
            else:
                s.flushInput() #svuoto il buffer
                print("the discharge ended unexpectedly before the expected discharge time, expected time and current time:", t_sim, t_ref)
                break

        # check azzeramento corrente di scarica
        iter = 0
        while iter <= 3:
            s.flushInput()
            ans_string = bytes.hex(s.read(19), ' ')
            print(ans_string)
            if ans_string.find("fa 00 00 00") != -1:
                print("Discharge ended")
                break
            else:
                print("Non-zero discharge current detected")
                iter += 1
                print("Repeat Check ")

        if iter == 3:
            print("Sending stop message to the load")
            s.write(bytes.fromhex(stop))


      except:
            print("Error while sending configuration, repeat connection to device")


def stop_meas(s):
    """
    Stop ongoing measure
    :param s: serial
    :return: None
    """
    try:
        print("Stop ongoing measure")
        s.write(bytes.fromhex(stop))

    except:
        print("Error while sending stop configuration, repeat connection to device")

    else:
        print('Stopped measure')


def disconnectserial_zke(s): # disconnessione dal dispositivo #[Chiusura seriale di comunicazione]
    """
    Close serial communication
    :param s: serial
    :return: None
    """
    try:
        print("Disconnecting from device [serial closing]")
        s.close()
    except:
        print("Error in closing serial, check if it is open")


def disconnectserial_andstop(s):
    """
    Stop measurement and close serial communication
    :param s: seriale
    :return: None
    """
    try:
        print("Disconnecting from device [serial closing and measure stop]")
        s.write(bytes.fromhex(stop))
        tm.sleep(1)  # obbligatorio per intercettare entrambi i messaggi
        s.write(bytes.fromhex(disconnect))
        s.close()
    except:
        print("Error while sending disconnect configuration, check if serial communication is open")




