# -*- coding: utf-8 -*-
"""
"""

category = 'Wavelength meter'                              #

class Driver_parser():                                     #
    def __init__(self, Instance, name, **kwargs):          #
        self.name     = name                               #
        self.Instance = Instance                           #


    def add_parser_usage(self,message):                    #
        """Usage to be used by the parser"""               #
        usage = f"""                                       #
{message}                                                  #
                                                           #
----------------  Examples:  ----------------              #
                                                           #
usage:    autolab driver [options] args                    #
                                                           #
    autolab driver -D {self.name} -A GPIB0::2::INSTR -C VISA -a 0.2
    load {self.name} driver using VISA communication protocol with address GPIB... and set the laser pump current to 200mA.
                                                           #
    autolab driver -D nickname -a 0.2
    Similar to previous one but using the device's nickname as defined in local_config.ini
            """                                            #
        return usage                                       #

    def add_parser_arguments(self,parser):                 #
        """Add arguments to the parser passed as input"""  #
        parser.add_argument("-w", "--wavelength", type=float, dest="wavelength", default=None, help="Reads the wavelength in nm." )
        parser.add_argument("-f", "--frequency", type=float, dest="frequency", default=None, help="Reads the frequency in THz." )
        parser.add_argument("-e", "--exposure", type=int, dest="exposure", default=None, help="Reads/sets the exposure in ms." )
        return parser                                      #

    def do_something(self,args):                           #
        if args.wavelength:                                 #
            # next line equivalent to: self.Instance.amplitude = args.amplitude
            getattr(self.Instance,'wavelength')(args.wavelength)
        if args.velocity:
            getattr(self.Instance,'frequency')(args.frequency)
        if args.acceleration:
            getattr(self.Instance,'exposure')(args.exposure)

    def exit(self):                                        #
        self.Instance.close()                              #