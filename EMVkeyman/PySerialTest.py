import serial


w2 = bytearray.fromhex('5669564F746563683200D00500001427')
print(w2.hex())
ser = serial.Serial('COM3', 19200, timeout = 2)
if ser.is_open == False:
    ser.open()
ser.write(w2)
temp = ser.readlines()
r2 = ''
for i in temp:
    r2 += i.hex()
print(r2)

