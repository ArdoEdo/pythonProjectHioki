from DSCAVM_encode import *
from hiokiprogrammer import *
from relay import *
import sys


def save_meas(meas_list, index, relax_meas):
    """
    Save the measurement on file
    :param list: meas_list
    :param index: index of meas to calc the SoC
    :param relax_meas: if the measurement is taken before or after resting
    :return: None
    """
    meas_dataframe = pd.DataFrame(columns=['Data'], data=list)
    meas_dataframe[['R', 'X', 'V', 'F']] = meas_dataframe.Data.str.split(",", expand=True)
    meas_dataframe = meas_dataframe.drop(columns=['Data'])
    print(meas_dataframe)
    if relax_meas:
        meas_dataframe.to_csv(dest_path + "IFR14500_SoC_" + str(max_SoC - index * delta_SoC) +"_A.csv")
    else:
        meas_dataframe.to_csv(dest_path + "IFR14500_SoC_" + str(max_SoC - index * delta_SoC) + "_B.csv")
    meas_list.clear()



# INPUT
config_path = "conf/conf.txt"
dest_path = "meas/"
freq_vect = [1.0, 2.0, 3.0, 5.0, 8.0, 10.0, 11.0, 21.0, 31.0, 61.0, 81.0, 100.0, 110.0, 210.0, 310.0, 510.0, 810.0, 1000.0]
log = 0
k = 1  # minutes of sleep for the second measure
max_SoC = 100
min_SoC = 90
delta_SoC = 10
n_cycle = len(range(min_SoC, max_SoC+delta_SoC, delta_SoC))
print("Number of measurement cycles", n_cycle)

# Comunicazione con i dispositivi
s = zke_conn()
print("Enter ZKE device configuration")
print("Discharge current value: [Ampere]")
test_val = float(input())
print("Minimum voltage value: [Volt]")
cutoff_volt = float(input())
print("Maximum discharge time value: [minutes]")
max_time = float(input())

print("Select the COM port on wich the Hioki device is connected:")
# CALC
port = input()
print("porta numero", port)
r = serial.Serial(port, baudrate=9600, timeout=0)
# setto lo HIOKI
read_conf(r, config_path)

print("Select the COM port on which the ESP8266 is connected.")
# CALC
port_esp = input()
r_conn = serial.Serial(port_esp, baudrate=9600, timeout=0)


# DATA
meas_list = []

# CALC
if log:
    logname = "logs/dsc_log.txt"
    sys.stdout = open(logname, 'a')

i = 0

while i < n_cycle:
    if i == 0:
        check_relay(r_conn, "ZKE_OFF")
        print("Start the EIS measures: ", i+1)
        start_EIS(r, freq_vect, meas_list)
    else:
        check_relay(r_conn, "ZKE_ON")
        print("Sending configuration to ZKE device:")
        new_conf(s, test_val, cutoff_volt, max_time)
        check_relay(r_conn, "ZKE_OFF")
        print("Start the EIS direct measures: ", i+1)
        start_EIS(r, freq_vect, meas_list)
        print("Start the resting phase lasting: " + str(k) +" minutes " )
        print("At time " + str(datetime.now()))
        tm.sleep(60*k)
        print("Start the EIS measurement after resting :")
        start_EIS(r, freq_vect, meas_list)
    #salvo su file
    meas_dataframe = pd.DataFrame(columns=['Data'], data=meas_list)
    meas_dataframe[['R', 'X', 'V', 'F']] = meas_dataframe.Data.str.split(",", expand=True)
    meas_dataframe = meas_dataframe.drop(columns=['Data'])
    print(meas_dataframe)
    meas_dataframe.to_csv(dest_path+"IFR14500_SoC_"+str(max_SoC-i*delta_SoC)+".csv")
    meas_list.clear() # resetto la variabile che contiene le misure per quell'SoC
    i += 1
