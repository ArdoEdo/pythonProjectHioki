from DSCAVM_encode import *
from hiokiprogrammer import *
from relay import *
import sys

"""Main codice sorgente del sistema di misura"""


# INPUT
config_path = "conf/conf.txt"
dest_path = "meas/"
freq_vect = [1.0, 2.0, 3.0, 5.0, 8.0, 10.0, 11.0, 21.0, 31.0, 61.0, 81.0, 100.0, 110.0, 210.0, 310.0, 510.0, 810.0, 1000.0]
log = 0
k = 7  # minuti di sleep per la seconda misura
# calcolo numero di cicli di scarica
max_SoC = 100
min_SoC = 10
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

print("Selezionare la porta COM su cui è collegato l'ESP8266 che controlla il relé:")
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
        print("Avvio le misure EIS del ciclo: ", i+1)
        start_EIS(r, freq_vect, meas_list)
    else:
        check_relay(r_conn, "ZKE_ON")
        print("Invio configurazione al dispositivo ZKE:")
        new_conf(s, test_val, cutoff_volt, max_time)
        check_relay(r_conn, "ZKE_OFF")
        print("Avvio la misura diretta EIS:")
        start_EIS(r, freq_vect, meas_list)
        print("Comincio la fase di riposo della durata di: " + str(k) +" minuti " )
        print("Alle ore " + str(datetime.now()))
        tm.sleep(60*k)
        print("Avvio la misura EIS dopo il riposo:")
        start_EIS(r, freq_vect, meas_list)
    #salvo su file
    meas_dataframe = pd.DataFrame(columns=['Data'], data=meas_list)
    meas_dataframe[['R', 'X', 'V', 'F']] = meas_dataframe.Data.str.split(",", expand=True)
    meas_dataframe = meas_dataframe.drop(columns=['Data'])
    print(meas_dataframe)
    meas_dataframe.to_csv(dest_path+"IFR14500_SoC_"+str(max_SoC-i*delta_SoC)+".csv")
    meas_list.clear() # resetto la variabile che contiene le misure per quell'SoC
    i += 1
