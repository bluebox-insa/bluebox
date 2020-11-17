import bluetooth
from subprocess import check_output

check_output(["/bin/echo -e 'power on\nscan on' | /usr/bin/bluetoothctl"], shell=True)

print("performing inquiry...")
# nearby_devices = bluetooth.discover_devices(duration=8, lookup_names=True, flush_cache=True, lookup_class=False)
nearby_devices = bluetooth.discover_devices(lookup_names=True)

print("found %d devices" % len(nearby_devices))

for addr, name in nearby_devices:
    try:
        print("  %s - %s" % (addr, name))
    except UnicodeEncodeError:
        print("  %s - %s" % (addr, name.encode('utf-8', 'replace')))
