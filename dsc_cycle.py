import numpy as np
from DSCAVM_encode import *
from hiokiprogrammer import *

# INPUT HIOKI
config_path = "conf/conf.txt"
dest_path = "meas/"
freq_vect = [1000, 800, 700, 500, 1.1]


# calcolo numero di cicli di scarica
max_SoC = 100
min_SoC = 50
delta_SoC = 10
n_cycle = len(range(min_SoC, max_SoC+delta_SoC, delta_SoC))
print("Numero di cicli di misura", n_cycle)

# Comunicazione con i dispositivi
print("Porte seriali disponibili, selezionare collegamento con carico attivo:")
s = zke_conn()
print("Inserire configurazione dispositivo ZKE")
print("Valore di corrente di scarica:")
test_val = float(input())  # Valore di corrente di scarica
print("Valore di tensione minima:")
cutoff_volt = float(input())
print("Valore tempo massimo di scarica:")
max_time = float(input())

print("Selezionare la porta COM su cui è collegato il dispotivo Hioki:")
# CALC
port = input()
r = serial.Serial(port, baudrate=9600, timeout=0)
# setto lo HIOKI
read_conf(r, config_path)

#DATA
meas_list = []
i = 0


while i < n_cycle:
    if i == 0:
        print("Avvio le misure EIS del ciclo: ", i+1)
        start_EIS(r, freq_vect, meas_list)
    else:
        print("Invio configurazione al dispositivo ZKE:")
        new_conf(s, test_val, cutoff_volt, max_time)
        print("Avvio le misure EIS:")
        start_EIS(r, freq_vect, meas_list)
    #salvo su file
    meas_dataframe = pd.DataFrame(columns=['Data'], data=meas_list)
    meas_dataframe[['R', 'X', 'V', 'F']] = meas_dataframe.Data.str.split(",", expand=True)
    meas_dataframe = meas_dataframe.drop(columns=['Data'])
    print(meas_dataframe)
    meas_dataframe.to_csv(dest_path+"IFR14500_SoC_"+str(min_SoC+i*10)+".csv")
    meas_list.clear() # resetto la variabile che contiene le misure per quell'SoC
    i += 1



