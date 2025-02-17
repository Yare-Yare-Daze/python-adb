from operator import ilshift
from random import Random, random, randrange
import sys
import io
import string
import time

from past.builtins import xrange

from boofuzz import helpers

import fastboot
import usb_exceptions
from boofuzz import *
from time import sleep

MAX_SIZE_CMD = 64
info_cb = fastboot.DEFAULT_MESSAGE_CALLBACK
successfull_mutations_list = []

class FastbootCommand(object):
    """Class commands for fastboot"""
    def __init__(self, strCmd, args = ''):
        self._isCmdOversized = False
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
        'mmcphase'
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
        'lock',  
        'enable-charger-screen', 
        'disable-charger-screen', 
        'off-mode-charge',
        'select-display-panel',
        'device-info',
        'poweroff',
        'reboot-recovery',
        'lkmsg',
        'lpmsg',
        'edl'
        ]
    cmd = cmdList[randrange(0, len(cmdList))]
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
    print('(Optional)Input arguments: ')
    stringArguments = input()

    fstcmd = FastbootCommand(stringCommand, stringArguments)
    if not fstcmd._isCmdOversized:
        fstcmd.CreatePucket()
    else:
        print('Error: Can\'t create pucket')
    return fstcmd

class RandomStringRange(Fuzzable):

    @staticmethod
    def CreateStringsListRange(start, final, amount_iterations):
        random = Random()
        list = []
        chr_start = ''
        chr_final = ''
        str = ''
        min_len = len(start)
        max_len = len(final)
        for i in range(amount_iterations+1):
            for j in range(0, random.randint(min_len, max_len)):
                if j >= min_len:
                    chr_start = string.ascii_lowercase[0]
                else:
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
    self, name=None, default_value="", start_str='aaa', final_str='zzz', max_mutations=100, expected_string_list=['aaa'], avoid_string_list=['flash'], *args, **kwargs
    ):
        default_value = helpers.str_to_bytes(default_value)

        super(RandomStringRange, self).__init__(name=name, default_value=default_value, *args, **kwargs)

        self.list_mutations = self.CreateStringsListRange(start_str, final_str, max_mutations)
        self.expected_string_list = expected_string_list
        self.avoid_string_list = avoid_string_list
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
        global amount_avoided_mutations
        amount_avoided_mutations = 0

        self.time_mutation = round(time.time(), 3)
        for i in range(0, self.get_num_mutations()):
            value = b""
            self.need_avoid_mutation = False
            
            for j in range(0, len(self.avoid_string_list)):
                if(self.list_mutations[i] == self.avoid_string_list[j]):
                    print("avoided: %s" % self.list_mutations[i])
                    self.need_avoid_mutation = True

            if self.need_avoid_mutation:
                amount_avoided_mutations += 1
                continue

            value += bytes(self.list_mutations[i], encoding="utf-8")
            yield value

            for j in range(0, len(self.expected_string_list)):
                if self.list_mutations[i] == self.expected_string_list[j]:
                    print('Finded expected string: %s' % self.expected_string_list[j])
                    print('Qualified name: %s' % self.qualified_name)
                    print('Stopped on %s index' % i)
                    self.time_mutation = round(time.time(), 3) - self.time_mutation
                    successfull_mutations_list.append(self.list_mutations[i])
                    successfull_mutations_list.append('Responce: %s' % fastboot.GetLastResponce())
                    successfull_mutations_list.append('Index: %s' % i)
                    successfull_mutations_list.append('Name: %s' % self.qualified_name)
                    successfull_mutations_list.append('Time: %s' % round(self.time_mutation, 3))
                    self.stop_mutations()
                    

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
    
    dev = fastboot.FastbootCommands()
    req = Request("Mutation-Getvar",children=(
            Block("Request-Line", children=(
            RandomStringRange(
                "RSRTest1", 
                default_value='none', 
                start_str='oem device-iaaa', 
                final_str='oem device-izzz', 
                max_mutations=2500, 
                expected_string_list=['oem device-info'],
                avoid_string_list=['oem device-iaaa', 'oem device-izzz']
                ),
            # RandomStringRange(
            #     "RSRTest2", 
            #     default_value='none', 
            #     start_str='oem unlaaa', 
            #     final_str='oem unlzzz', 
            #     max_mutations=1500, 
            #     expected_string_list=['oem unlock'],
            #     avoid_string_list=['oem unlaaa', 'oem unlzzz']
            #     ),
            # RandomStringRange(
            #     "RSRTest3", 
            #     default_value='none', 
            #     start_str='oem laaa', 
            #     final_str='oem lzzz', 
            #     max_mutations=1500, 
            #     expected_string_list=['oem lock'],
            #     avoid_string_list=['oem laaa', 'oem lzzz']
            #     ),
            RandomStringRange(
                "RSRTest4", 
                default_value='none', 
                start_str='getvar:caa', 
                final_str='getvar:czz', 
                max_mutations=2500, 
                expected_string_list=['getvar:version', 'getvar:variant', 'getvar:product', 'getvar:secure', 'getvar:token', 'getvar:crc']
                ),
            RandomStringRange(
                "RSRTest0", 
                default_value='none', 
                start_str='getvar:a', 
                final_str='getvar:zzzzzzzz', 
                max_mutations=2500, 
                expected_string_list=['getvar:version', 'getvar:variant', 'getvar:product', 'getvar:secure', 'getvar:token']
                ),
            RandomStringRange(
                "RSRTest5",
                default_value='none',
                start_str='aaaoot-bootloader',
                final_str='zzzoot-bootloader',
                max_mutations=2500,
                expected_string_list=['reboot-bootloader']
                ),
            RandomStringRange(
                "RSRTest6",
                default_value='none',
                start_str='rebaaa',
                final_str='rebzzz',
                max_mutations=2500,
                expected_string_list=['reboot']
                ),
            RandomStringRange(
                "RSRTest7",
                default_value='none',
                start_str='getvar:a',
                final_str='getvar:azz',
                max_mutations=2500,
                expected_string_list=['getvar:all']
                ),
            # RandomStringRange(
            #     "RSRTest7",
            #     default_value='none',
            #     start_str='a',
            #     final_str='zzzzzzzz',
            #     max_mutations=1500,
            #     expected_string_list=['getvar', 'reboot', 'oem'],
            #     avoid_string_list=['continue', 'flash', 'erase', 'download', 'flashall']
            #     ),
            ))
        ))

    for device in dev.Devices():
        
        print('Serial number: %s' % device.serial_number)
        print('Port puth: %s' %device.port_path)
        print('Usb_info: %s' %device.usb_info)

        device.Open()
        print('Opened USB device!')

        device.FlushBuffers()
        print('FlushBuffered')

        protocol = fastboot.FastbootProtocol(device)
        print('Created class object FastbootProtocol')
    
        amount_sended_mutations = 0
        total_time = round(time.time(), 3)

        for mut in req.mutations('none'):
            amount_sended_mutations += 1

            for mutt in mut:
                tuple = mutt.value.partition(b':')
                pucket = FastbootCommand(tuple[0].decode('utf-8'), tuple[2].decode('utf-8'))
                #pucket = FastbootCommand(mutt.value.decode('utf-8'))
                pucket.CreatePucket()
                
                print('Pucket command bytes: %s' % pucket.GetCommandBytes())
                try:
                    protocol._Write(pucket.GetBufferedCommand(), len(pucket.GetCommand()))
                except usb_exceptions.WriteFailedError as err:
                    total_time = round(time.time(), 3) - total_time
                    print('Error: %s' % err)
                    print('Amount of sended mutatuions: %s' % amount_sended_mutations)
                    print('Anount of avoided mutations: %s' % amount_avoided_mutations)
                    print('Amount of all mutations %s' % str(amount_sended_mutations + amount_avoided_mutations))
                    print('All time: %s' % round(total_time, 3))
                    print('Expected mutations list (empty if not catched any expected string):')
                    print(successfull_mutations_list)
                    return
                else:
                    print(protocol.HandleSimpleResponses())
                    #print(protocol._AcceptResponses(b'OKAY', info_cb))

        total_time = round(time.time(), 3) - total_time
        print('Amount of sended mutatuions: %s' % amount_sended_mutations)
        print('Anount of avoided mutations: %s' % amount_avoided_mutations)
        print('Amount of all mutations %s' % str(amount_sended_mutations + amount_avoided_mutations))
        print('All time: %s' % round(total_time, 3))
        print('Expected mutations list (empty if not catched any expected string):')
        print(successfull_mutations_list)

if __name__ == '__main__':
    sys.exit(main())