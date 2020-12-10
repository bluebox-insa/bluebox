from bluetool import Bluetooth

bluetooth = Bluetooth()



print("---------------------------------")

ADDR_BOSE_REVOLVE = '2C:41:A1:97:16:0C'
ADDR_BOSE_SOUNDLINK   = '00:0C:8A:E2:08:8D'

#connect speaker one to adapter interface hci1
print(bluetooth.pair(address=ADDR_BOSE_REVOLVE, adapter_idx=1))
print(bluetooth.connect(address=ADDR_BOSE_REVOLVE, adapter_idx=1))

#connect speaker one to adapter interface hci0
print(bluetooth.pair(address=ADDR_BOSE_SOUNDLINK, adapter_idx=0))
print(bluetooth.connect(address=ADDR_BOSE_SOUNDLINK, adapter_idx=0))

print(bluetooth.get_connected_devices())