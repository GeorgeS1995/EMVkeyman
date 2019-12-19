f = open('popka')
keyRID = []
keyIndex = []
keyHashalgo = []
keyPkAlgo = []
keyChecksum = []
keyExponent = []
keyModLength = []
keyModulux = []
i = -1
temp1 = ''
commands = []

for line in f:
    startpars = line.find('=') + 1
    if line == '.End\n':
        i += 1
        keyModulux.append(temp1)
        temp1 = ''
    elif line.find('.RID') != -1 :
        keyRID.append(line[startpars: -1])
    elif line.find('.Index') != -1:
        keyIndex.append(line[startpars: -1])
    elif line.find('.HashAlgo') != -1:
        keyHashalgo.append(line[startpars: -1])
    elif line.find('.PkAlgo') != -1:
        keyPkAlgo.append(line[startpars: -1])
    elif line.find('.Checksum') != -1:
        keyChecksum.append(line[startpars:-1])
    elif line.find('.Exponent') != -1:
        temp0 = line[startpars: -1].replace(' ', '')
        keyExponent.append(temp0.zfill(8))
    elif line.find('.ModLength') != -1:
        keyModLength.append(line[startpars: -1])
    elif line.find('.') == -1 and line.find('#') == -1:
        temp1 += line[: -1]


f.close()

while i >= 0:
    temp2 = keyRID[i] + keyIndex[i] + keyHashalgo[i] + keyPkAlgo[i] + keyChecksum[i] + keyExponent[i] + keyModLength[i] + keyModulux[i]
    commands.append(temp2.replace(' ', ''))
    i -= 1

print(commands[0])
temp3 = hex(len(commands[0]) // 2)[2::].upper().zfill(4)
print(temp3 + commands[0])
print(i)