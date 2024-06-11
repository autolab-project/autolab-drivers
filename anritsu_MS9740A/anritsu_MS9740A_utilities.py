#!/usr/bin/env python3
# -*- coding: utf-8 -*-

category = 'Optical Spectrum Analyzer (OSA)'

class Driver_parser():
    def __init__(self, Instance, name, **kwargs):
        self.name     = name
        self.Instance = Instance
        
        
    def add_parser_usage(self,message):
        """Usage to be used by the parser"""
        usage = f"""
{message}

----------------  Examples:  ----------------

usage:    autolab driver [options] args
        
    autolab driver -D {self.name} -A TCPIP::192.168.0.3::INSTR -C VISA -m some_methods
    Execute some_methods of the driver. A list of available methods is present at the top of this help.
    
    autolab driver -D nickname -m some_methods
    Same as before using the nickname defined in local_config.ini
            """
        return usage
    
    def add_parser_arguments(self,parser):
        """Add arguments to the parser passed as input"""
        #parser.add_argument("-c", "--channels", type=str, dest="channels", default=None, help="Set the traces to act on/acquire from." )
        #parser.add_argument("-o", "--filename", type=str, dest="filename", default=None, help="Set the name of the output file" )
        #parser.add_argument("-F", "--force",action="store_true", dest="force", default=None, help="Allows overwriting file" )
        #parser.add_argument("-t", "--trigger", dest="trigger",action="store_true", help="Trigger the scope once" )
        
        return parser

    def do_something(self,args):
        #if args.filename:
            ##getattr(self.Instance,'get_data_traces')(traces=args.channels,single=args.trigger)
            #getattr(self.Instance,'get_data_traces')(traces=args.channels)
            #getattr(self.Instance,'save_data_traces')(filename=args.filename,traces=args.channels,FORCE=args.force)
        pass

    def exit(self):
        self.Instance.close()
