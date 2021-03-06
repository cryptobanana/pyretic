#!/usr/bin/python

from time import time, sleep
from subprocess import call, check_output, Popen, PIPE, STDOUT, CalledProcessError
import sys as sys
import os as os
from optparse import OptionParser
from signal import SIGINT

from threading import Thread

class subprocess_output(Thread):
    
    def __init__(self,proc):
        self.proc = proc
        Thread.__init__(self)

    def run(self):
        while self.proc.poll() is None:
            line = self.proc.stdout.readline()
            print line,
            sleep(0.1)


def parseArgs():
    """Parse command-line args and return options object.
    returns: opts parse options dict"""
    if '--custom' in sys.argv:
        index = sys.argv.index( '--custom' )
        if len( sys.argv ) > index + 1:
            filename = sys.argv[ index + 1 ]
            self.parseCustomFile( filename )
        else:
            raise Exception( 'Custom file name not found' )

    desc = ( "The %prog utility creates Mininet network from the\n"
             "command line. It can create parametrized topologies,\n"
             "invoke the Mininet CLI, and run tests." )

    usage = ( '%prog [options]\n'
              '(type %prog -h for details)' )
    
    opts = OptionParser( description=desc, usage=usage )
    opts.add_option( '--verbosity', '-v', type='choice',
                     choices=['quiet','verbose'], default = 'quiet',
                     help = '|'.join( ['quiet','verbose'] )  )
    opts.add_option( '--controller', '-c', action="store", type="string", 
                     dest="controller_src", default='hub.py', help = 'the pyretic controller to use'  )
    opts.add_option( '--unit-test', '-u', action="store", type="string", 
                     dest="unit_test", default='connectivity_test.py', help = 'the unit test to use'  )

    options, args = opts.parse_args()
    return (options, args)

def main():
    
    (options, args) = parseArgs()
    if options.verbosity == 'verbose':
        verbose = ['-v','verbose']
    else:
        verbose = []

    # GET PATHS
    unit_test_path = os.path.realpath(options.unit_test)
    controller_src_path = os.path.realpath(options.controller_src)
    pox_path = os.path.expanduser('~/pox/pox.py')

    # MAKE SURE WE CAN SEE ALL OUTPUT IF VERBOSE
    env = os.environ.copy()
    if verbose:
        env['PYTHONUNBUFFERED'] = 'True'

    # STARTUP CONTROLLER
    controller = Popen([sys.executable, pox_path,'--no-cli', controller_src_path], 
                       env=env,
                       stdout=PIPE, 
                       stderr=STDOUT)
    if verbose:
        controller_out = subprocess_output(controller)
        controller_out.start()
    sleep(1)

    # TEST EACH TOPO
    topos = ['single,2','single,4','single,16','linear,2','linear,4','linear,8','tree,2,2','tree,2,3','tree,3,2']

    for topo in topos:
        test = ['sudo', unit_test_path, '--topo', topo] + verbose
        testproc = call(test)
        if testproc == 0:
            print "%s\tCONNECTIVITY PASSED" % topo
        else:
            print "%s\tCONNECTIVITY FAILED" % topo
        
    # KILL CONTROLLER
    controller.send_signal( SIGINT )

if __name__ == '__main__':
    main()
