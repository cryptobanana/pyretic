
################################################################################
# The Frenetic Project                                                         #
# frenetic@frenetic-lang.org                                                   #
################################################################################
# Licensed to the Frenetic Project by one or more contributors. See the        #
# NOTICES file distributed with this work for additional information           #
# regarding copyright and ownership. The Frenetic Project licenses this        #
# file to you under the following license.                                     #
#                                                                              #
# Redistribution and use in source and binary forms, with or without           #
# modification, are permitted provided the following conditions are met:       #
# - Redistributions of source code must retain the above copyright             #
#   notice, this list of conditions and the following disclaimer.              #
# - Redistributions in binary form must reproduce the above copyright          #
#   notice, this list of conditions and the following disclaimer in            #
#   the documentation or other materials provided with the distribution.       #
# - The names of the copyright holds and contributors may not be used to       #
#   endorse or promote products derived from this work without specific        #
#   prior written permission.                                                  #
#                                                                              #
# Unless required by applicable law or agreed to in writing, software          #
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT    #
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the     #
# LICENSE file distributed with this work for specific language governing      #
# permissions and limitations under the License.                               #
################################################################################

##############################################################################################################################
# TO TEST EXAMPLE                                                                                                            #
# -------------------------------------------------------------------                                                        #
# start mininet:  pyretic/mininet.sh --topo=gateway                                                                          #
# run controller: pox.py --no-cli pyretic/examples/kitchen_sink.py                                                           #
# test:           pingall                                                                                                    #
##############################################################################################################################

from frenetic.lib import *

from examples.mac_learner import mac_learner
from examples.hub import hub
from examples.arp import arp, ARP
from examples.load_balancer import static_lb, lb
from examples.firewall import fw
from virttopos.gateway import GatewayVirt
from virttopos.bfs import BFS

def in_(l):
    return union([match(switch=s) for s in l])

def gateway_example(num_clients,num_servers):

    ethernet = [2,3,4,1000]
    ip_core  = [5,6,7,1002]
    gateway  = [1001]

    gw_mac = MAC('AA:AA:AA:AA:AA:AA')

    eth_prefix = '10.0.0.'
    ip_prefix  = '10.0.1.'

    eth_macs = { IP(eth_prefix+str(i+1)) : MAC('00:00:00:00:00:0'+str(i)) \
                      for i in range(1,1+num_clients) }
    eth_macs.update({IP(eth_prefix+'1') : gw_mac})

    ip_macs = { IP(ip_prefix+str(i+1)) : MAC('00:00:00:00:00:0'+str(i+num_clients)) \
                        for i in range(1,1+num_servers) }
    ip_macs.update({IP(ip_prefix +'1') : gw_mac})
    
    all_macs = dict(eth_macs.items() + ip_macs.items())

    def rewrite_dstmac(tm):
        return parallel([match(dstip=k)[pop('dstmac') >> push(dstmac=v)] for k,v in tm.items()])

    def rewrite_srcmac():
        return pop('srcmac') >> push(srcmac=gw_mac)
    
    def rewrite_macs(tm):
        return rewrite_dstmac(tm) >> rewrite_srcmac()

    def fix_dstmac():
        fix = parallel([(match(dstip=k) & ~match(dstmac=v))[pop('dstmac') >> push(dstmac=v)] for k,v in ip_macs.items()])
        pas = intersect([~(match(dstip=k) & ~match(dstmac=v)) for k,v in ip_macs.items()])[passthrough]
        return fix | pas

    public_ip = '10.0.1.100'
    fake_mac = MAC('BB:BB:BB:BB:BB:BB')

    all_macs.update({IP(public_ip) : fake_mac})

    R = [ip_prefix + str(i) for i in range(2, 2+num_servers)]
    H = {eth_prefix + str(i) : 0 for i in range(2,2+num_clients)}
    W = {(c,public_ip) for c in H.keys()}
    from_client = union([match(srcip=c) for c in H.keys()])

    eth_pol = if_(ARP,arp(eth_macs),mac_learner())
    alb =     dynamic(lb)(public_ip,R,H) >> fix_dstmac() 
    afw =     dynamic(fw)(W) 
    ip_pol =  if_(from_client, afw >> alb, alb >> afw) >> mac_learner() 
    ip_pol =  virtualize(ip_pol,BFS(ip_core))
   
##   CIDR MATCHING CURRENTLY NOT WORKING
#    eth_to_ip = match(inport=1,dstip='10.0.0.0/24')
#    ip_to_eth = match(inport=2,dstip='10.0.1.0/24')

    to_eth = union([ match(dstip='10.0.0.'+str(i)) for i in range(2,2+num_clients) ])
    to_ip  = union([ match(dstip='10.0.1.'+str(i)) for i in range(2,2+num_servers) ])

    eth_to_ip = match(inport=1) & (to_ip | match(dstip=public_ip) )
    ip_to_eth = match(inport=2) & (to_eth)

    gw = if_(ARP,arp(eth_macs), 
             rewrite_macs(all_macs) >> 
             ( eth_to_ip[fwd(2)] | ip_to_eth[fwd(1)] ))


    ## COMMENT THIS OUT TO SEE PACKET HANDLING PRINTOUTS
    return in_(ethernet)[ eth_pol ]  | \
        in_(gateway)[ gw ] | \
        in_(ip_core)[ ip_pol ]

    return in_(ethernet)[ pprint('->eth') >> eth_pol >> pprint('eth->') ]  | \
        in_(gateway)[ pprint('->gw') >> gw >> pprint('gw->') ] | \
        in_(ip_core)[ pprint('->ip') >> ip_pol >> pprint('ip->') ]
            
@dynamic
def vgateway_example(self,num_clients,num_servers):
    ge = gateway_example(num_clients,num_servers)
    self.policy = virtualize(ge, GatewayVirt(Recurse(self)))


def main(clients='3',servers='3'):
    clients = int(clients)
    servers = int(servers)
    #return gateway_example(clients,servers)   # topo=pgateway
    return vgateway_example(clients,servers)   # topo=gateway

