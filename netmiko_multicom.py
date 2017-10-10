#!/usr/bin/env python3

'''
this Script is designed to take a yaml input of hosts and a list of commands. 
It will log into each of devices and return the outputs/resuls of the commands
It has some exception handling and sanitising of inputs but still use at your own risk. 
Scott Rowlandson
scott@soram.org
'''

import os
import sys
import argparse
from netmiko import ConnectHandler
from netmiko.ssh_exception import NetMikoTimeoutException
import yaml
from paramiko.ssh_exception import SSHException, ProxyCommandFailure
from getpass import getpass


def netmiko_create_conn(hostname, user, paswd, devicetype):
    #execute connect handler to connect to device
    try:
        return(ConnectHandler(device_type = devicetype, host = hostname, username = user, password = paswd, secret = paswd, ssh_config_file = "~/.ssh/config"))
    except (EOFError, SSHException, ProxyCommandFailure, NetMikoTimeoutException, Exception):
        print('SSH is not enabled for this device '+ hostname +'\n')
        return(False)


def netmiko_close_conn(connection):
    return(connection.disconnect())


def netmiko_findp(connection):
    #Check connection is still valid
    if connection.find_prompt(): 
        #print('#######SUCCESSFULL##########')
        return(True)
    else:
        #print('########FAILED##############')
        print('Connection failed to node: '+ host +'\n')
        return(False)


def sanitise_input(com_list):
    #search the comm_list of any instances of bad commands i.e. conf t, set, delete etc returns bolean!
    sanitise_list = ['conf', 'set', 'delete', 'modify'] # add to list for additional commands to be excluded
    for line in sanitise_list: 
        for com in com_list:
            if line in com:
                return(True)
    return(False)
                


def netmiko_send(connection, com_list):
    #check connection is still valid
    if netmiko_findp(connection):
        output = []
        for item in com_list:
            print('***Executing command: '+item +'\n')
            com_return = connection.send_command(item)
            output.append(com_return)
            print('***Success\n')
        return(dict(zip(com_list, output)))


def main(arguments):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-y', '--infile', type=str, help='Input Yaml comands', required = True)
    parser.add_argument('-o', '--outfile', type=str, help='Outfile path', required = False, default = '')
    parser.add_argument('-u', '--username', type=str, help='ssh username', required = True, default = '')

    args = parser.parse_args()
    password = getpass()
    output = []
    

    ####Open the yaml input file
    with open(args.infile,'rb') as in_file:
        yam_in = yaml.load(in_file)

    #Sanitise input to check that there no malicious commands (more checks to be added here)
    if sanitise_input(yam_in['command_list']):
        print('badcommand')
        sys.exit('Bad input for commands')
    else: #if input is OK -> continue
        for node in yam_in['nodes']:
            connection = netmiko_create_conn(node['host'], args.username, password, node['type'])
            if connection:
                print('***Executing commands on '+node['host']+':\n')
                connection.enable()
                com_log = netmiko_send(connection, yam_in['command_list'])
                output.append(com_log)
                with open(args.outfile + node['host']+'.txt', 'w') as outfile:
                    outfile.write('Command output for host: '+ node['host']+'\n\n')
                    for item in yam_in['command_list']:
                        outfile.write('************************************************************\n')
                        outfile.write('********** Command output for ' + item + ' ****************\n\n')
                        outfile.write(com_log[item]+'\n\n')
                connection.exit_enable_mode()
            else:
                print('Skipping '+node['host']+' no connection established\n\n')

        ## If you want to do something else with output here it is saved as a array of dictionaries
	## each array entry is per host
	## each host has a dictionary in the form {command:output}



if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
