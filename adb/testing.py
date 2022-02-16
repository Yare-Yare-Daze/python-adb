from random import random, randrange
import sys
import io
from adb import fastboot
import adb_commands
import common
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
    cmdList = ['devices', 'continue', 'download', 'erase', 'flash', 'getvar', 'oem', 'reboot', 'reboot-bootloader', 'flashall']
    getvarArgs = ['all', 'version', 'serialno', 'product', 'platform', 'modelid', 'cidnum', 'security', 'boot-mode', 'build-mode', 'version-bootloader', 'cid']
    flashArgs = ['userdata', 'system', 'boot', 'radio', 'recovery']
    oemArgs = ['unlock', 'unlock-go', 'lock', 'writecid', 'writeimei', 'get_identifier_token', 'enable-charger-screen', 'disable-charger-screen', 'off-mode-charge']
    cmd = cmdList[randrange(0, len(cmdList))]
    args = ''
    if cmd == 'getvar':
        args = getvarArgs[randrange(0, len(getvarArgs))]
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

def main():
    puck = GeneratePucketFromInput()
    dev = fastboot.FastbootCommands()
    for device in dev.Devices():
        print(device.serial_number)
        print(device.port_path)
        print(device.usb_info)
        print(puck.GetBufferedCommand())
        device.Open()
        print('Opened USB device!')
        device.FlushBuffers()
        print('FlushBuffered')
        protocol = fastboot.FastbootProtocol(device)
        print('Created fastboot.FastbootProtocol')
        protocol._Write(puck.GetBufferedCommand(), len(puck.GetCommand()))
        print('Successfully send data')
        protocol._AcceptResponses(b'OKAY', info_cb)
        print('Accepted response')
    """while True:
        sleep(2)
        pucket = RandomGeneratePucket()
        print('Pucket class: %s' % pucket)
        print('Pucket command: %s' % pucket.GetCommand())
        print('Pucket command bytes: %s' % pucket.GetCommandBytes())
        print('Pucket BytesIO: %s' % pucket.GetBufferedCommand())
        print('Pucket BytesIO.getbuffer(): %s' % pucket.GetBufferedCommand().getbuffer())"""

if __name__ == '__main__':
    sys.exit(main())