from crccheck.crc import Crc16CcittFalse


def create_command(command, data):
    temp = bytearray.fromhex('5669564F746563683200' + command + data)
    crc = Crc16CcittFalse()
    crc.process(temp)
    crchex = crc.finalhex()
    i = len(crchex) - 1
    cheksum = ''
    while i > 0:
        cheksum = cheksum + crchex[i - 1] + crchex[i]
        i -= 2
    print(temp)
    print(cheksum)
    return temp + cheksum

print(create_command('1800', '0000'))