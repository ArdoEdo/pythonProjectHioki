

string = ":SAMPLE:DELAY:WAVE 3.0" + '\r\n'
string2 = ":SYSTEM:RESET"

print(string)
print("stampo la lunghezza prima della partizione", len(string))

string = string.split(' ', 1)[0] + '\r\n' #elimino parametro di settaggio e aggiungo il fineriga
print(string)
print("stringa dopo partizione lunghezza:", len(string)) #stampo lunghezza senza parametro

print(string)

"""index = string.index("\r\n") # trovo indice fineriga

print("indice fineriga", string.index("\r\n"))
string = string[:index] + '?' + string[index:]

print(string)
print(string.index("\r\n"))
"""