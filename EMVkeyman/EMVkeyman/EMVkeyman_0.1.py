import curses
import curses.textpad
import serial
import sys
import glob
import time
from crccheck.crc import Crc16CcittFalse


class MenuHandler:
    def __init__(self, list_point, list_func):
        self.list_point = list_point
        self.list_func = list_func
        self.current_crd = 0

    def print_menu(self, stdscr):
        # рисуем пункты
        # Уберает мерцание курсора
        curses.curs_set(0)
        # Определяю размеры окна
        h, w = stdscr.getmaxyx()
        # Задачем сцетовую гамму
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
        for ind, row in enumerate(self.list_point):
            # x и y указывают на центр окна для текста text
            x = w // 2 - 20
            y = h // 2 + ind
            # отвечает за цветовое выделение выбранного блока
            if ind == self.current_crd:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(y, x, row)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(y, x, row)

    def cursor_moving(self, stdscr):
        self.print_menu(stdscr)
        while True:
            key = stdscr.getch()
            if key == curses.KEY_UP:
                self.current_crd -= 1
                if self.current_crd < 0:
                    self.current_crd = len(self.list_point) - 1
            elif key == curses.KEY_DOWN:
                self.current_crd += 1
                if self.current_crd >= len(self.list_point):
                    self.current_crd = 0
            elif key == curses.KEY_ENTER or key in [10, 13]:  # Ввод везде в силу особенностей ОС работает по разному
                self.enter_press()
            self.print_menu(stdscr)

    def enter_press(self):
        for ind, row in enumerate(self.list_func):
            if ind == self.current_crd:
                curses.wrapper(row)

    @staticmethod
    def any_key_press(stdscr):
        key = stdscr.getch()
        if key != None:
            curses.wrapper(main_menu)


class OneFuncEnter(MenuHandler):
    ''' По нажатию enter подставляюет в нужную функцию параметр'''

    def enter_press(self):
        # Даже когда заработает сделай красивее
        stdscr = curses.initscr()
        for ind, row in enumerate(self.list_func):
            if ind == self.current_crd:
                curses.wrapper(VivopayProto.Baudrate_changer(VivopayProto(), stdscr, row))


class VivopayProto:
    COM = ''
    BaudRate = 0
    BaudRateList = ['9600', '19200', '38400', '57600', '115200']
    def __init__(self):
        pass

    def create_command(self, command, data = '0000'):
        """ Конструктор комманд для вивы
            command - команда по дукоментации
            data - данные, для команд где неиспользуется '0000', длинна подаваемых данных считается отдельно
            :return команду + CRC
        """
        if data != '0000':
            temp0 = hex(len(data) // 2)[2::].upper().zfill(4)
            data = temp0 + data
        temp1 = ('5669564F746563683200' + command + data)
        crc = Crc16CcittFalse()
        crc.process(bytearray.fromhex(temp1))
        crchex = crc.finalhex()
        i = len(crchex) - 1
        cheksum = ''
        while i > 0:
            cheksum = cheksum + crchex[i - 1] + crchex[i]
            i -= 2
        return temp1 + cheksum

    def COM_Handler(self, COM, BaudRate, command, delay = 0.2):
        command = bytearray.fromhex(command)
        ser = serial.Serial(COM, BaudRate, timeout=delay)
        if ser.is_open == False:
            ser.open()
        ser.write(command)
        temp = ser.readlines()
        r2 = ''
        # цикл склеивает полученные строчки из буфера COM порта
        for i in temp:
            r2 += i.hex()
        return r2

    def serial_ports(self):
        """ Lists serial port names

            :raises EnvironmentError:
                On unsupported or unknown platforms
            :returns:
                A list of the serial ports available on the system
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result

    def vivo_find(self):
        COMports = self.serial_ports()
        for COMport in COMports:
            for i in VivopayProto.BaudRateList:
                temp = self.COM_Handler(COMport, i, self.create_command('1801'))
                if temp == '5669564f74656368320018000000fa83':
                    VivopayProto.COM = COMport
                    VivopayProto.BaudRate = str(i)
                    break

    def Baudrate_changer(self, stdscr, BaudRate):
        # создает кнопку для смены частоты
        BaudRateDict = {'9600' : '01', '19200' : '02', '38400' : '03', '57600' : '04', '115200' : '05'}
        self.COM_Handler(VivopayProto.COM, VivopayProto.BaudRate, self.create_command('3001', BaudRateDict[BaudRate]))
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        stdscr.addstr(h // 2 - 1, w // 2 - 20,'BaudRate changed to {}'.format(BaudRate))
        stdscr.refresh()
        curses.wrapper(main_menu)

    def list_RIDS(self):
        temp = 28
        RIDs = []
        command = self.COM_Handler(VivopayProto.COM, VivopayProto.BaudRate, self.create_command('D006'), 0.5)
        if command == '5669564f746563683200d0000000cce4':
            RIDs = 'RIDs not found'
        else:
            while temp < len(command):
                RIDs.append(command[temp:temp + 10])
                temp += 10
            RIDs.pop()
        return RIDs

    def list_indices(self):
        if self.list_RIDS() == 'RIDs not found':
            pass
        else:
            output = []
            for i, value in enumerate(self.list_RIDS()):
                Currentkey = self.COM_Handler(VivopayProto.COM, VivopayProto.BaudRate, self.create_command('D007', value))
                temp = list(Currentkey.partition(value)[2])
                temp1 = ''
                i = 0
                while i < (len(temp) - 4):
                        temp1 += '['
                        temp1 += temp[i]
                        i += 1
                        temp1 += temp[i]
                        i += 1
                        temp1 += ']'
                        temp1 += ' '
                output.append(temp1)
            return output

    def delet_all_key(self):
        temp = self.COM_Handler(VivopayProto.COM, VivopayProto.BaudRate, self.create_command('D005'), 1)
        if temp == '5669564f746563683200d0000000cce4':
            output = 'All keys deleted successfully'
        else:
            output = 'Something went wrong'
        return output

    def read_keys_from_file(self, file):
        f = open(file)
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
            elif line.find('.RID') != -1:
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
            temp2 = keyRID[i] + keyIndex[i] + keyHashalgo[i] + keyPkAlgo[i] + keyChecksum[i] + keyExponent[i] + \
                    keyModLength[i] + keyModulux[i]
            commands.append(temp2.replace(' ', ''))
            i -= 1
        return commands


# Пункты меню, редактирую их не забывать редактировать main_menu_actions и комментить функции для кнопок
text_main_menu = ('1. Change BaudRate', '2. Output the existing keys','3. Delet_all_key', '4. Writing the keys from file', '5. Save the existing keys to file', '6. Exit')


# куча заглушек для пунктов главного меню
def Change_BaudRate(stdscr):
    if VivopayProto.BaudRate != 0:
        # стряпую список доступных скоростей
        avalaible_baudrate = []
        for i in VivopayProto.BaudRateList:
            if i != VivopayProto.BaudRate:
                   avalaible_baudrate.append(i)
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        stdscr.addstr(h//2 - 1, w//2 - 20, 'list avalaible baudrate:')
        # Да я тут одно и тоже передаю как 2 разных поля, ПЕРЕДЕЛАТЬ КРАСИВО
        return_buttom = OneFuncEnter(avalaible_baudrate, avalaible_baudrate)
        return_buttom.print_menu(stdscr)
        return_buttom.cursor_moving(stdscr)
        stdscr.refresh()
    else:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        stdscr.addstr(h // 2 - 1, w // 2 - 20, 'Vivopay Kiosk not found')
        curses.wrapper(main_menu)
        stdscr.refresh()


def Output_the_existing_keys(stdscr):
    result = VivopayProto()
    RIDs = result.list_RIDS()
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    stdscr.addstr(h // 2 - 1, w // 2 - 20, 'RIDs: {}'.format(RIDs))
    Indices = result.list_indices()
    if Indices == None:
        y = 0
        pass
    else:
        for i, value in enumerate(Indices):
            y = h // 2 + i
            stdscr.addstr(y, w // 2 - 20, 'RID {0} Indices: {1}'.format(RIDs[i],value))
        y = len(RIDs)
    stdscr.addstr(h // 2 + y + 1, w // 2 - 11, 'Press any key to return')
    MenuHandler.any_key_press(stdscr)
    stdscr.refresh()


def Delet_all_key(stdscr):
    def delet_output(stdscr):
        stdscr.clear()
        # Определяю размеры окна
        h, w = stdscr.getmaxyx()
        action = VivopayProto()
        stdscr.addstr(h // 2 - 1, w // 2 - 20, action.delet_all_key())
        curses.wrapper(main_menu)
        stdscr.refresh()
    text_exit_menu = ('yes', 'no')
    delet_cinfirm_menu_actions = (delet_output, main_menu)
    stdscr.clear()
    # Определяю размеры окна
    h, w = stdscr.getmaxyx()
    stdscr.addstr(h//2 - 1, w//2 - 20, 'Confirm deletion of all keys')
    exit_menu = MenuHandler(text_exit_menu, delet_cinfirm_menu_actions)
    exit_menu.print_menu(stdscr)
    exit_menu.cursor_moving(stdscr)
    stdscr.refresh()


def Writing_the_keys_from_file(stdscr):
    parsed_file = VivopayProto()
    h, w = stdscr.getmaxyx()
    stdscr.keypad(1)
    stdscr.clear()
    stdscr.addstr(h // 2 - 1, w // 2 - 20, 'Enter file name:')
    curses.cbreak()
    # enable keypad mode
    stdscr.keypad(1)
    stdscr.refresh()
    win = curses.newwin(1, 60, h // 2, w // 2 - 20)
    tb = curses.textpad.Textbox(win)
    file = tb.edit()
    temp = parsed_file.read_keys_from_file(file)
    for i in temp:
        temp1 = parsed_file.COM_Handler(VivopayProto.COM, VivopayProto.BaudRate, parsed_file.create_command('D003', i), 1)
        if temp1 == '5669564f746563683200d0000000cce4':
            stdscr.clear()
            stdscr.addstr(h // 2 - 1, w // 2 - 20, 'key successfully written: {}'.format(i))
            stdscr.refresh()
        else:
            stdscr.clear()
            stdscr.addstr(h // 2 - 1, w // 2 - 20, 'Something went wrong')
            stdscr.refresh()
    curses.wrapper(main_menu)


def Save_the_existing_keys_to_file():
    pass


#def Test(stdscr):
    # Туn я буду тестировать выводы команд, потом удалю
    #result = VivopayProto()
    #stdscr.clear()
    # Определяю размеры окна
    #h, w = stdscr.getmaxyx()
    #stdscr.addstr(h // 2 - 1, w // 2 - 20, result.read_keys_from_file('popka')[0] )
    #time.sleep(5)
    #curses.wrapper(main_menu)
    #stdscr.refresh()

def Exit(stdscr):
    # Определяю функции и текст для меню выхода из программы
    text_exit_menu = ('yes', 'no')
    exit_menu_actions = (exit, main_menu)
    stdscr.clear()
    # Определяю размеры окна
    h, w = stdscr.getmaxyx()
    stdscr.addstr(h//2 - 1, w//2 - 20, 'Are you sure to exit?')
    exit_menu = MenuHandler(text_exit_menu, exit_menu_actions)
    exit_menu.print_menu(stdscr)
    exit_menu.cursor_moving(stdscr)
    stdscr.refresh()


main_menu_actions = (Change_BaudRate, Output_the_existing_keys, Delet_all_key, Writing_the_keys_from_file, Save_the_existing_keys_to_file, Exit)


# Рисуею главное меню
def main_menu(stdscr):
    result = VivopayProto()
    result.vivo_find()
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    main_menu = MenuHandler(text_main_menu, main_menu_actions)
    if VivopayProto.COM != '' or VivopayProto.BaudRate != 0:
        stdscr.addstr(h // 2 - 2, w // 2 - 20, 'Current COM: {0}, Current BaudRate: {1}'.format(VivopayProto.COM, VivopayProto.BaudRate))
    else:
        stdscr.addstr(h // 2 - 2, w // 2 - 20, 'Vivopay Kiosk not found')
    main_menu.print_menu(stdscr)
    main_menu.cursor_moving(stdscr)
    stdscr.refresh()


curses.wrapper(main_menu)
