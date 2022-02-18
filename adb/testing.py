from random import random, randrange
import sys
import io
import string

from past.builtins import xrange

from boofuzz import helpers

import fastboot
from boofuzz import *
from time import sleep

MAX_SIZE_CMD = 64
info_cb = fastboot.DEFAULT_MESSAGE_CALLBACK

class FastbootCommand(object):
    """Class commands for fastboot"""

    _isCmdOversized = False

    def __init__(self, strCmd, args = ''):
        self._strCommand = strCmd + args
        if len(self._strCommand) <= MAX_SIZE_CMD:
            if args:
                self._strCommand = '%s:%s' % (strCmd, args)
            else:
                self._strCommand = strCmd
        else:
            self._isCmdOversized = True
            print("Error: Command length is too big!")

    def CreatePucket(self):
        if not self._isCmdOversized:
            self._strCommandBytes = bytes(self._strCommand, encoding=('utf8'))
            self._strBufferedCommand = io.BytesIO(self._strCommandBytes)
            return self._strBufferedCommand

    def GetCommand(self):
        if not self._isCmdOversized:
            return self._strCommand
    
    def GetCommandBytes(self):
        if not self._isCmdOversized:
            return self._strCommandBytes    
    
    def GetBufferedCommand(self):
        if not self._isCmdOversized:
            return self._strBufferedCommand

def getHelp():
    strHelp = "Fastboot Commands: \n"
    strHelp += "devices, continue, download, erase, flash, getvar, oem, reboot, reboot-bootloader, flashall\n"
    strHelp += "Args: \n"
    strHelp += "For oem: unlock, unlock-go, lock, writecid, writeimei, get_identifier_token, enable-charger-screen, disable-charger-screen, off-mode-charge\n"
    strHelp += "For flash: userdata, system, boot, radio, recovery"
    strHelp += "For getvar: all, version, serialno, product\n"

    return strHelp

def RandomGeneratePucket():
    cmdList = [
        'continue', 
        'download', 
        'erase', 
        'flash', 
        'getvar', 
        'oem', 
        'reboot', 
        'reboot-bootloader', 
        'flashall'
        ]
    getvarArgs = [
        'all', 
        'version', 
        'serialno', 
        'product', 
        'token',
        'battery-soc-ok', 
        'battery-voltage', 
        'secure',
        'variant',
        'off-mode-charge', 
        'charger-screen-enabled', 
        'max-download-size', 
        'crc',
        'mmcphase',
        'karnel',
        ]
    flashArgs = [
        'userdata', 
        'system', 
        'boot', 
        'radio', 
        'recovery'
        ]
    oemArgs = [
        'unlock', 
        'unlock-go', 
        'lock', 
        'writecid', 
        'writeimei', 
        'get_identifier_token', 
        'enable-charger-screen', 
        'disable-charger-screen', 
        'off-mode-charge'
        ]
    #cmd = cmdList[randrange(0, len(cmdList))]
    cmd = 'getvar'
    args = ''
    if cmd == 'getvar':
        args = getvarArgs[randrange(0, len(getvarArgs))]
        # args = list[1].get_value()
    elif cmd == 'oem':
        args = oemArgs[randrange(0, len(oemArgs))]
    elif cmd == 'flash':
        args = flashArgs[randrange(0, len(flashArgs))]
    fstcmd = FastbootCommand(cmd, args)
    fstcmd.CreatePucket()
    return fstcmd

def GeneratePucketFromInput():
    """Генерирует пакеты из команд, введенных с консоли."""
    print('Input command (help or h): ')
    stringCommand = input()
    if stringCommand == 'help' or stringCommand =='h':
        print(getHelp())
        return 
    print('(Optional)Input arguments: ')
    stringArguments = input()

    fstcmd = FastbootCommand(stringCommand, stringArguments)
    if not fstcmd._isCmdOversized:
        fstcmd.CreatePucket()
    else:
        print('Error: Can\'t create pucket')
    return fstcmd

def CreateListAAAZZZ():
    list = []
    for i in string.ascii_lowercase:
        before = ''
        before += i
        for j in string.ascii_lowercase:
            before = before[:1]
            before += j
            for z in string.ascii_lowercase:
                before = before[:2]
                before += z
                list.append(before)

    return list

class RandomStringRange(Fuzzable):

    @staticmethod
    def CreateStringsListRange(start, final, length, amount_iterations):
        list = []
        chr_start = ''
        chr_final = ''
        str = ''
        for i in range(amount_iterations+1):
            for j in range(length):
                chr_start = start[j]
                chr_start_num = ord(chr_start)
                chr_final = final[j]
                chr_final_num = ord(chr_final)
                if chr_start_num <= chr_final_num:
                    chr_random = chr(randrange(chr_start_num, chr_final_num+1))
                else:
                    chr_random = chr(randrange(chr_final_num, chr_start_num+1))
                str += chr_random
            list.append(str)
            str = ''    
        return list

    def __init__(
    self, name=None, default_value="", start_str='aaa', final_str='zzz', max_mutations=100, expected_string='aaa', *args, **kwargs
    ):
        default_value = helpers.str_to_bytes(default_value)

        super(RandomStringRange, self).__init__(name=name, default_value=default_value, *args, **kwargs)

        self.list = self.CreateStringsListRange(start_str, final_str, len(start_str), max_mutations)
        self.expected_string = expected_string
        self.amount_mutation = 0
        self.max_mutations = max_mutations
        self.start_str = start_str
        self.final_str = final_str

    def mutations(self, default_value):
        """
        Mutate the primitive value returning False on completion.

        Args:
            default_value (str): Default value of element.

        Yields:
            str: Mutations
        """
        for i in range(0, self.get_num_mutations()):
            value = b""
            self.amount_mutation += 1
            value += bytes(self.list[i], encoding="utf-8")
            if self.list[i] == self.expected_string:
                print('Did this')
                return
            yield value


    def encode(self, value, mutation_context):
        return value

    def num_mutations(self, default_value):
        """
        Calculate and return the total number of mutations for this individual primitive.

        Args:
            default_value:

        Returns:
            int: Number of mutated forms this primitive can take
        """

        return self.max_mutations

def main():
    # pucket = GeneratePucketFromInput()
    # if pucket.GetCommand() == 'help' or pucket.GetCommand() == 'h':
    #     print(getHelp())
    #     return
    dev = fastboot.FastbootCommands()


    req = Request("Mutatuion-Getvar",children=(
            Block("Request-Line", children=(
            #Group("Getvar-Args", values=l),
            #FromFile("TestFromFile", 'none', filename="C:/Users/EremeevMikhail/Documents/python-adb/adb/file.txt")
            RandomStringRange("RSRTEST", default_value='none', start_str='aaa', final_str='zzz', max_mutations=3000, expected_string='crc'),
            #RandomData(name="TEST", default_value='AAA', min_length=3, max_length=3),
            ))
        ))

    for device in dev.Devices():

    # count = 0
    # index = 0

    # for mut in req.get_mutations():
    #     print(mut)
    #     for mutt in mut:
    #         if mutt.value == b"all" or mutt.value == b"cid":
    #             count += 1
    #             req.stop_mutations()
    #             index = mutt.index
    #     if count > 0:
    #         break  

        print('Serial number: %s' % device.serial_number)
        print('Port puth: %s' %device.port_path)
        print('Usb_info: %s' %device.usb_info)

        device.Open()
        print('Opened USB device!')

        # device.FlushBuffers()
        # print('FlushBuffered')

        protocol = fastboot.FastbootProtocol(device)
        print('Created class object FastbootProtocol')
        counter = 0
        mutatuions = 0
        # while True:
        for mut in req.get_mutations():
            for mutt in mut:
                mutatuions += 1
                # sleep(1)
                pucket = FastbootCommand('getvar', mutt.value.decode('utf-8'))
                pucket.CreatePucket()
                #print('Pucket class: %s' % pucket)
                print('Pucket command: %s' % pucket.GetCommand())
                print('Pucket command bytes: %s' % pucket.GetCommandBytes())
                #print('Pucket BytesIO: %s' % pucket.GetBufferedCommand())
                #print('Pucket BytesIO.getbuffer(): %s' % pucket.GetBufferedCommand().getbuffer())

                protocol._Write(pucket.GetBufferedCommand(), len(pucket.GetCommand()))
                print('Successfully send data')

                protocol._AcceptResponses(b'OKAY', info_cb)
                print(protocol.GetLastResponce())
                print('Accepted response')
                if mutt.value == b"all" or mutt.value == b"crc":
                    counter += 1
                    return
                print(counter)
                print()
        print('Amount of mutations: %s' % mutatuions)

if __name__ == '__main__':
    sys.exit(main())