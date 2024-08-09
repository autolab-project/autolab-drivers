""" In this program there are several functions that explore the TTI
 functionalities as well its drivers in aimtti_TGF3162.py """

import numpy as np
import time
import matplotlib.pyplot as plt
from aimtti_TGF3162 import Driver_SOCKET, Driver_VISA


def main():
    """ In this example we send an arbitrary waveform to the TTI and set it as output on channel 1.
    You can easily see the effect on the oscilloscope """
    set_arbitrary_waveform()

    """ In this example we modulate the frequency of channel 2 using the external modulation option. In this case, the external
    modulation is provided by channel 1, that is triggered when we want. You can easily see the effect on the oscilloscope """
    external_modulation()

    """ In this example we implement a triggered sweep in frequency. For the parameters set it is better to look at the beating on a photodiode """
    sweep()

    """ In this example we implement a simple modulation. For the parameters set it is better to look at the beating on a photodiode """
    modulation()


def set_arbitrary_waveform():
    """ function that shows how to send an arbitary wavefrom to the TTI and use that waveform as output """
    # create TTI object
    driver = Driver_SOCKET(address='192.168.1.23', port=9221, nb_channels=2)
    # driver = Driver_VISA(address='TCPIP::192.168.1.23::9221::SOCKET', nb_channels=2)

    # check driver status
    print("IDN: "+str(driver.idn()))

    # reset driver
    driver.reset()

    # get channel 1 of driver
    ch1 = driver.channel1

    # create waveform and transform it to the correct range
    nbpts = 2**(8) # number of point in array. The maximum number according to TTI manual is 8192 = 2**(13)
    x = np.linspace(-3, 3, nbpts)
    waveform = np.abs(np.sin(x)) + 5*np.exp(-np.power(x, 100))*np.cos(x)

    # define waveform in ARB 3 with name Rui and with interpolation off
    ch1.arbitrary_waveform.define_waveform(3, "Rui", "OFF")

    # send waveform to ARB3 slot memory
    ch1.arbitrary_waveform.send_waveform(waveform, 3)
    time.sleep(1)

    # download wavform and plot
    waveform = ch1.arbitrary_waveform.read_waveform(3)
    plt.plot(waveform)
    plt.show()

    # set ARB3 waveform as output
    ch1.arbitrary_waveform.load_waveform(3)  # Could also use "Rui" to load_waveform ARB3 as it has been defined before
    ch1.frequency(1e3)

    # set output on
    ch1.set_output("ON")

    # close driver connection
    driver.close()


def external_modulation():
    """ function to example how to execute a "triggered" modulation using the external modulation option
    We use channel 1 to send a waveform that will be the external modulation source for channel 2 """
    # create TTI object
    # driver = Driver_SOCKET(address='192.168.1.23', port=9221, nb_channels=2)
    driver = Driver_VISA(address='TCPIP::192.168.1.23::9221::SOCKET', nb_channels=2)

    # check driver status
    print("IDN: "+str(driver.idn()))

    # reset driver
    driver.reset()

    # get channels objects
    ch2 = driver.channel2
    ch1 = driver.channel1

    # create waveform and transform it to the correct range
    nbpts = 2**(8) # number of point in array. The maximum number according to TTI manual is 8192 = 2**(13)
    x = np.linspace(-50, 50, nbpts)
    waveform = np.sin(x / 5)

    # send waveform to ARB3 slot memory
    ch1.arbitrary_waveform.send_waveform(waveform, 3)  # Could also use 'ARB3'
    time.sleep(0.5)

    # download waveform and plot
    waveform = ch1.arbitrary_waveform.read_waveform(3)
    plt.plot(waveform)
    plt.show()

    # set burst mode in channel 1 and arbitrary carrier waveform 3 as output
    ch1.arbitrary_waveform.load_waveform(3)
    ch1.frequency(0.1)
    ch1.burst.set_trigger_source("MAN") # Set the burst trigger source to manual
    ch1.burst.set_type("NCYC")
    ch1.burst.set_count(1)

    # in channel 2 set sine as waveform in with external modulation mode
    ch2.set_mode("SINE")
    ch2.frequency(10e3)
    ch2.amplitude(1)
    ch2.modulation.set_type("FM")
    ch2.modulation.set_fm_source("EXT")
    ch2.modulation.set_fm_deviation(5e3)

    # set output on on both channels. For channel 1, it will output only when triggered.
    ch1.set_output("ON")
    ch2.set_output("ON")

    # wait for 2 seconds to give us time to check signal on oscilloscope
    time.sleep(2)

    # trigger channel 1
    print("Trigger channel 1 ...")
    ch1.trigger()

    # close driver connection
    driver.close()



def sweep():
    """ function that shows how to do a triggered sweep in frequency """

    # create TTI object
    driver = Driver_SOCKET(address='192.168.1.23', port=9221, nb_channels=2)
    # driver = Driver_VISA(address='TCPIP::192.168.1.23::9221::SOCKET', nb_channels=2)

    # check driver status
    print("IDN: "+str(driver.idn()))

    # reset driver
    driver.reset()

    # get channels objects
    ch1 = driver.channel1
    ch2 = driver.channel2

    # set sine waveform on channel 1 and 2
    ch1.set_mode("SINE")
    ch1.frequency(200e6)
    ch2.set_mode("SINE")
    ch2.frequency(200e6)

    # set output on
    ch1.set_output("ON")
    ch2.set_output("ON")

    print("Setting trig ...")
    time.sleep(2)

    # set sweep on channel 1
    ch1.sweep.set_state("ON")
    ch1.sweep.set_type("LINUP")
    ch1.sweep.set_mode("TRIG")
    ch1.sweep.set_trigger_source("MAN")  # Set the sweep trigger source to manual
    ch1.sweep.set_stop(200e6+100e3)  # you must first set the end frequency and only after the start frequency
    ch1.sweep.set_start(200e6)
    ch1.sweep.set_time(10)

    # trigger sweep
    time.sleep(1)
    print("Sweep trig ...")
    ch1.trigger()
    # driver.write_to_channel(1, "*WAI")  # Useless for this instrument
    ch1.sweep.set_state("OFF")

    time.sleep(1)

    # close driver connection
    driver.close()


def modulation():
    """ function that shows how to do modulation using and arbitrary waveform """
    # create TTI object
    # driver = Driver_SOCKET(address='192.168.1.23', port=9221, nb_channels=2)
    driver = Driver_VISA(address='TCPIP::192.168.1.23::9221::SOCKET', nb_channels=2)

    # check driver status
    print("IDN: "+str(driver.idn()))

    # reset driver
    driver.reset()

    # get channels objects
    ch1 = driver.channel1
    ch2 = driver.channel2

    # create arbitrary waveform
    nbpts = 2**(8) # number of point in array. The maximum number according to TTI manual is 8192 = 2**(13)
    x = np.linspace(-50, 50, nbpts)
    waveform = np.tanh(x / 10) + 1

    # send arbitrary waveform to ARB 3
    ch2.arbitrary_waveform.send_waveform(waveform, 3)

    # downaload waveform from ARB3 and plot it
    waveform = ch2.arbitrary_waveform.read_waveform(3)
    plt.plot(waveform)
    plt.show()

    # set sine wave on channel 1 and 2
    ch1.set_mode("SINE")
    ch1.frequency(200e6)
    ch2.set_mode("SINE")
    ch2.frequency(200e6)

    # set modulation on channel 1
    ch1.modulation.set_fm_shape("ARB3")
    ch1.modulation.type("FM")
    ch1.modulation.set_fm_deviation(10000)
    ch1.modulation.set_fm_frequency(100)

    # set output on
    ch2.set_output("ON")
    ch1.set_output("ON")

    # close driver connection
    driver.close()


if __name__ == '__main__':
    main()
