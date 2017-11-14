#!/usr/bin/env python3

"""
this Script is designed to take a yaml input of hosts and a list of commands.
It will log into each of devices and return the outputs/resuls of the commands
It has some exception handling and sanitising of inputs but still use at your
own risk.
Scott Rowlandson
scott@soram.org
"""

import argparse
from getpass import getpass
from netmiko import ConnectHandler
from netmiko.ssh_exception import NetMikoTimeoutException
import os
from paramiko.ssh_exception import SSHException, ProxyCommandFailure
import sys
import yaml



def netmiko_create_conn(hostname: object, user: object, paswd: object, devicetype: object) -> object:
    #execute connect handler to connect to device
    try:
        return ConnectHandler(device_type = devicetype,
                              host = hostname,
                              username = user,
                              password = paswd,
                              secret = paswd,
                              ssh_config_file ="~/.ssh/config")
    except (EOFError, SSHException, ProxyCommandFailure,
            NetMikoTimeoutException, Exception):
        print('SSH is not enabled for this device '+ hostname +'\n')
        return False


def netmiko_close_conn(connection):
    return connection.disconnect()


def netmiko_findp(connection):
    #Check connection is still valid
    if connection.find_prompt(): 
        #print('#######SUCCESSFULL##########')
        return True
    else:
        #print('########FAILED##############')
        print('Connection failed to node: '+ host +'\n')
        return False


def sanitise_input(com_list):
    '''
    search the comm_list of any instances of bad commands
    # i.e. conf t, set, delete etc
    If found it exists the program
    '''
    sanitise_list = ['conf', 'set', 'delete', 'modify']
    for line in sanitise_list: 
        for com in com_list:
            if line in com:
                print('Bad command {}'.format(line))
                sys.exit('BAD commands exiting....')
                

def netmiko_send(connection, com_list):
    #check connection is still valid
    if netmiko_findp(connection):
        output = []
        for item in com_list:
            print('***Executing command: '+item +'\n')
            com_return = connection.send_command(item)
            output.append(com_return)
            print('***Success\n')
        return dict(zip(com_list, output))

def save_multi(path: object, outdict: object) -> object:
    '''
    Function to save each element of the dictionary as a separate output file

    :param path: output file path name
    :type path: str
    :param outdict: dictionary containing key, and output str
    :type outdict: dict[str:str]
    :return:
    '''
    file_count = 1
    for key in outdict.keys():
        with open(path+filecount+'.txt','w') as outfile:
            outfile.write('Output of command {}:\n\n'.format(key))
            outfile.writelines(outdict[key])


def parse_options():
    ''' CLI argument parser function for standalone use

    This function will take the arguments from the CLI and set them
    as module variables.

    If no options are passed, the default behaviour will be to print the
    arguments available to the user.

    @return parser.parse_args(): The CLI options for use in main()
    @rtype parser.parse_args(): list
    '''
    parser = argparse.ArgumentParser()
    parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    required.add_argument(
        '--infile',
        dest='INFILE',
        help='Input YAML commands',
        required = True)
    required.add_argument(
        '--outpath',
        dest='OUTPATH',
        help='Outfile Path',
        required=True)
    required.add_argument(
        '--username',
        dest='USERNAME',
        help='Username to log into devices',
        required=True)
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    return parser.parse_args()


def main(args):
    password = getpass()
    output = []
    ####Open the yaml input file
    with open(args.INFILE,'rb') as in_file:
        yam_in = yaml.load(in_file)

    sanitise_input(yam_in['command_list'])
    for node in yam_in['nodes']:
        connection = netmiko_create_conn(node['host'],args.USERNAME,
                    password,node['type'])
        if connection:
            print('***Executing commands on:\n'.format(node['host']))
            if node['type'] in ('cisco_ios','cisco_asa'):
                connection.enable()
            com_log = netmiko_send(connection, yam_in['command_list'])
            output.append(com_log)
            save_multi(args.OUTPATH + '/' + node, com_log)

            if node['type'] in 'cisco_ios': #exit enable mode if required
                connection.exit_enable_mode()
        else:
            print('Skipping '+node['host']+' no connection established\n\n')



if __name__ == "__main__":
    main(parse_options())
