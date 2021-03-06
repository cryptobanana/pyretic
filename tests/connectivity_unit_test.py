#!/usr/bin/python

from unit_util import *

def fullConnectivity(hosts,results):

    for h1 in hosts:
        for h2 in hosts:
            try:
                # IF ALL PINGS FAILED FOR ANY HOST PAIR
                # CONNECTIVITY FAILS
                if results[h1.name][h2.name] == 0:
                    return False
            except KeyError:
                pass    
    
    return True


def parseArgs():
    """Parse command-line args and return options object.
    returns: opts parse options dict"""
    parseCustomFile(os.path.expanduser('~/pyretic/mininet/extra-topos.py'))
    
    desc = ( "The %prog utility creates Mininet network from the\n"
             "command line. It can create parametrized topologies,\n"
             "invoke the Mininet CLI, and run tests." )

    usage = ( '%prog [options]\n'
              '(type %prog -h for details)' )
    
    opts = OptionParser( description=desc, usage=usage )
    addDictOption( opts, TOPOS, TOPODEF, 'topo' )
    opts.add_option( '--verbose', '-v', action="store_true", dest="verbose")
    opts.add_option( '--quiet', '-q', action="store_true", dest="quiet")
    opts.add_option( '--ping-type', '-p', type='choice',
                     choices=['ICMP','TCP80SYN'], default = 'ICMP',
                     help = '|'.join( ['ICMP','TCP80SYN'] )  )
    opts.add_option( '--ping-pattern', '-P', type='choice',
                     choices=['sequential','intermediate','parallel'], default = 'sequential' ,
                     help = '|'.join( ['sequential','intermediate','parallel'] )  )
    opts.add_option( '--count', '-c', action="store", type="string", 
                     dest="count", default='1', help = 'number of ping attempts'  )
    options, args = opts.parse_args()

    if options.quiet and options.verbose:
        opts.error("options -q and -v are mutually exclusive")
    return (options, args)


def main():

    (options, args) = parseArgs()

    ## SET LOGGING AND CLEANUP PREVIOUS MININET STATE, IF ANY
#    lg.setLogLevel('info')
    cleanup()

    ## SET UP TOPOLOGY
    topo = buildTopo( TOPOS, options.topo )

    ## SET UP MININET INSTANCE AND START
    net = Mininet( topo, switch=OVSKernelSwitch, host=Host, controller=RemoteController )
    net.start()
    if options.verbose:  print "Mininet started"

    # WAIT FOR CONTROLLER TO HOOK UP
    # TODO - PARAMETERIZE WAIT BASED ON NUMBER OF LINKS
    sleep(WARMUP)

    # RUN TESTS
    if options.verbose:  print "Test beginning"
    start = time()
    results = ping_all(net,options.verbose,options.ping_type,options.count,options.ping_pattern)
    elapsed = time() - start
    if options.verbose:  print "Test done, processing results"
    connectivity = fullConnectivity(net.hosts,results)

    if not options.quiet:
        if connectivity:
            print "%s\tCONNECTIVITY PASSED\t%s" % (options.topo,elapsed)
        else:
            print "%s\tCONNECTIVITY FAILED\t%s" % (options.topo,elapsed)

    ## SHUTDOWN MININET
    net.stop()

    if connectivity:
        sys.exit(0)
    else:
        sys.exit(-1)
            
    
if __name__ == '__main__':
    main()
