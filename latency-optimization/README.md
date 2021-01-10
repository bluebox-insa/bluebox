# Things you can do to reduce latency problems

## Adjust buffer size
As explained [here](https://bugs.freedesktop.org/show_bug.cgi?id=58746) latency may increases due to bluetooth instabilities.

Pulseaudio provides several parameters to configure your systems. See [here](https://www.systutorials.com/docs/linux/man/5-pulse-daemon.conf/) for more details.

### Reasons

> Every time signal degrades audio gets more out of sync - up to about 10-15 seconds (if I remember correctly.
I've debugged bluez5 pulseaudio module and suspect that the problem lies in buffering for bluetooth socket. Here's my analysis:

1) Pulseaudio detects BT signal drop when write() on bluetooth socket returns EAGAIN (i.e., when the buffer is full).
2) Bluetooth socket buffer is quite big (by default)
3) When pulseaudio stops sending audio packets to BT socket the buffer still contains a lot of packets
4) pulseaudio considers those packets as successfully sent - but they aren't
5) BT connection seems to never be able to "catch up" with the amount of buffered packets and audio becomes out-of-sync.

One way to partially solve this is to decrease the **buffer size as much as possible**. 

Setting a smaller buffer size  works best. This ensures that audio lag won't accumulate after BT signal degradation while preventing audio skipping due to buffer underruns. Audio still may skip (sometimes several times in a row) - but without the lag after BT signal restores.

### Steps

1. Open the config file
    ```bash
    sudo vim /etc/pulse/daemon.conf
    ```

1. Scroll down (almost till the end of the file)

    You should find these lines

    ```bash
    ; fragments = 4
    ; nb_ms = 250
    ```

1. Change these values and uncomment that way

    ```bash
    fragments = 2 # /!\ line is now uncommented (no ";" at the beginning)
    nb_ms = 125
    ```

    > These values may not be the best ones for your configuration but you can try with that first.

    `default-fragments` The default number of fragments. Defaults to 4.

    `default-fragment-size-msec` The duration of a single fragment. Defaults to 25ms (i.e. the total buffer is thus 100ms long).