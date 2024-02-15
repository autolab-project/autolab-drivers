category = 'Lockin Amplifier'                              #

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
    autolab driver -D {self.name} -A GPIB0::2::INSTR -C VISA 
    load {self.name} driver using VISA communication protocol with address GPIB...
                                                           #
    autolab driver -D nickname
    Similar to previous one but using the device's nickname as defined in local_config.ini
            """                                            #
        return usage                                       #

    def add_parser_arguments(self,parser):                 #
        """Add arguments to the parser passed as input"""  #
        parser.add_argument("-a", "--amplitude", type=str, dest="amplitude", default=None, help="Get the amplitude" )

        return parser                                      #

    def do_something(self,args):                           #
        if args.amplitude:                                 #
            # next line equivalent to: self.Instance.amplitude = args.amplitude
            getattr(self.Instance,'amplitude')(args.amplitude)

    def exit(self):                                        #
        self.Instance.close()                              #