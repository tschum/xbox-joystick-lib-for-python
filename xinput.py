from ctypes import *
from ctypes.wintypes import *
from enum import Enum
import sys

class xinput():
    def __init__(self,player=0):
        if player > 3 or player < 0:
            raise Exception("Player number must be in the range 0 to 3")
        self.player = player
        try:
                self.xi_lib = cdll.LoadLibrary(r"XInput1_4.dll")
        except Exception as err:
                print("Could not read lib {}".format(err))
        class XINPUT_GAMEPAD(Structure):
                _fields_ =[("wButtons",WORD),("bLeftTrigger",c_ubyte),
                ("bRightTrigger",c_ubyte),("sThumbLX",SHORT),("sThumbLY",SHORT),("sThumbRX",SHORT),("sThumbRY",SHORT)]
        class XINPUT_STATE(Structure):
                _fields_ =[("dwPacketNumber",DWORD),
                ("Gamepad",XINPUT_GAMEPAD)]
        self.BUTTON_NAME_VALUE  ={  0:"None",1:'jpUp',2:'jpDn',4:'jpLeft',8:'jpRight',16:'start',32:'back',64:'LS',
                    128:'RS',256:'LB',512:'RB',1024:'Future1',2048:'Future2', 4096:'A',8192:'B',16384:'X',32768:'Y'}
        self.buttons_down =[]
        self.last_packet = -1
        self.thumbSlack = 3000
        self.state = XINPUT_STATE()
        self.poll()

    def connected(self):
        self.ret_val = self.xi_lib.XInputGetState(self.player,pointer(self.state))
        return self.ret_val==0

    def poll(self):
        self.connected()
        if self.ret_val == 0: # xbox stick is conected
            self.update_buttons()
        else:
            self.buttons_down = []
        return self.ret_val == 0,self.buttons_down

    def update_buttons(self):
        self.last_packet = self.state.dwPacketNumber
        self.buttons_down=[ {self.BUTTON_NAME_VALUE[key]: key}
                        for key in self.BUTTON_NAME_VALUE.keys()
                        if key & self.state.Gamepad.wButtons ]
        if self.state.Gamepad.bRightTrigger!=0:
                self.buttons_down.append({'RT':
                                        self.state.Gamepad.bRightTrigger})
        if self.state.Gamepad.bLeftTrigger!=0:
                self.buttons_down.append({'LT':
                                        self.state.Gamepad.bLeftTrigger})

        if True in [abs(i) - self.thumbSlack > 0 for i in [
                self.state.Gamepad.sThumbLX,
                self.state.Gamepad.sThumbLY]]:
            self.buttons_down.append( { 'LTS': (
                                    self.state.Gamepad.sThumbLX,
                                    self.state.Gamepad.sThumbLY )})

        if True in [ abs(i) - self.thumbSlack > 0 for i in [
                self.state.Gamepad.sThumbRX,
                self.state.Gamepad.sThumbRY]]:
            self.buttons_down.append({'RTS': (
                                    self.state.Gamepad.sThumbRX,
                                    self.state.Gamepad.sThumbRY )})

    def BatteryLevel (self):
        class XINPUT_BATTERY_INFORMATION(Structure):
                _fields_ =[("BatteryType",BYTE),("BatteryLevel",BYTE)]
        class BATTERY_DEVTYPE(Enum):
            _GAMEPAD=0x00
            _HEADSET=0x01
        class BATTERY_TYPE(Enum):
            _DISCONNECTED = 0x00    # This device is not connected
            _WIRED  = 0x01    # Wired device, no battery
            _ALKALINE  = 0x02    # Alkaline battery source
            _TYPE_NIMH  =  0x03    # Nickel Metal Hydride battery source
            _TYPE_UNKNOWN =  0xFF    # Cannot determine the battery type
        # These are only valid for wireless, connected devices, with known battery types
        # The amount of use time remaining depends on the type of device.
        class BATTERY_LEVEL(Enum):
            _EMPTY = 0x00
            _LOW = 0x01
            _MEDIUM = 0x02
            _FULL = 0x03
        class BATTERY_ERROR(Enum):
            _S_OK = 0
            _DEVICE_NOT_CONNECTED = 1167
        self.battery = XINPUT_BATTERY_INFORMATION()
        ret_val = self.xi_lib.XInputGetBatteryInformation(self.player,
            BYTE(BATTERY_DEVTYPE._GAMEPAD.value),
            pointer(self.battery))
        if ret_val == BATTERY_ERROR._S_OK.value:
            return ret_val, "Battery type is {} level is {}.".format(
                BATTERY_TYPE(self.battery.BatteryType).name,
                BATTERY_LEVEL(self.battery.BatteryLevel).name)
        else:
            return ret_val, "Error reading battery {}.".format(
                BATTERY_ERROR(ret_val).name)


if '-test' in sys.argv:
    player = [xinput(i) for i in range(4)]
    for i in range(len(player)):
        er_code, bat_data = player[i].BatteryLevel()
        if (er_code != 1167):
            print(bat_data)

    while True in [i.connected() for i in player]:
        for i in range(len(player)):
            change,value = player[i].poll()
            if change and len(value)>0:
                print("player={}".format(i),value)

    print("xinput shows no devices connected.")
