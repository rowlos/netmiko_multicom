#!/usr/bin/env python3

"""
This is a netmiko multicom class, it is designed to take a
this Script is designed to take a yaml input of hosts and a list of commands.
It will log into each of devices and return the outputs/resuls of the commands
It has some exception handling and sanitising of inputs but still use at your own risk.
Scott Rowlandson
scott@soram.org
"""
import getpass
import os
import sys
import argparse
from netmiko import ConnectHandler
from netmiko.ssh_exception import NetMikoTimeoutException
import yaml
from paramiko.ssh_exception import SSHException, ProxyCommandFailure
from getpass import getpass


class NetCom:
    def __init__(self, hostname, user, devtype, command):

        self.hostname = hostname
        self.user = user
        self.devtype = devtype
        self.passwd = getpass()
        try:
            self.conn = ConnectHandler(device_type=self.devtype, host=self.hostname, username=self.user,
                                       password=self.passwd, secret=self.passwd, ssh_config_file="~/.ssh/config")
            print(self.conn)
        except (EOFError, SSHException, ProxyCommandFailure, NetMikoTimeoutException, Exception):
            print('SSH is not enabled for this device ' + self.hostname + '\n')
            sys.exit()
        self.outdict = {}
        self.multi_commands = []


    def __enter__(self):
        if commands:
            self.command = command
        else:
            sys.exit('no commands entered')
        self.netmiko_send_single()

    def __exit__(self, type, value, traceback):
        # make sure the ssh connection is closed.
        #print(self.outdict())
        self.conn.close()

    def netmiko_close_conn(self):
        self.conn.disconnect()

    def netmiko_findp(self):
        # Check connection is still valid
        if self.conn.find_prompt():
            # print('#######SUCCESSFULL##########')
            return True
        else:
            # print('########FAILED##############')
            print('Connection failed to node: ' + host + '\n')
            return False

    def sanitise_input(self):
        # search the comm_list of any instances of bad commands i.e. conf t, set, delete etc returns bolean!
        sanitise_list = ['conf', 'set', 'delete', 'modify']  # add to list for additional commands to be excluded
        for line in sanitise_list:
            for com in self.multi_commands:
                if line in com:
                    return True
        return False

    def netmiko_send(self):
        # check connection is still valid
        print(self.conn)
        if self.netmiko_findp():
            if self.sanitise_input:
                output = []
                self.conn.enable()
                for item in self.multi_commands:
                    print('***Executing command: ' + item + '\n')
                    com_return = self.conn.send_command(item)
                    output.append(com_return)
                    print('***Success\n')
                self.outdict = dict(zip(com_list, output))
                self.conn.exit_enable_mode()
                
    def netmiko_send_multi(self):
        #sends a single command and prints
        if self.netmiko_findp():
            print(self.conn.send_command(self.command))

def parse_options():
    """ CLI argument parser function for standalone use This function will take the arguments from the CLI and set them
    as module variables. If no options are passed, the default behaviour will be to print the
    arguments available to the user. @return parser.parse_args(): The CLI options for use in main()
    @rtype parser.parse_args(): list
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--hostname',
        dest='HOSTNAME',
        help='hostname of device to connect to')
    parser.add_argument(
        '--username',
        dest='USERNAME',
        help='username used to log in')
    parser.add_argument(
        '--type',
        dest='TYPE',
        help='type of device')
    parser.add_argument(
        '--commands',
        dest='COMMANDS',
        help='list of commands to be executed'),
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    return parser.parse_args()


def main(args):
    """The instantiation of the Netcom instance.

    @param args: The arguments supplied via the CLI
    @type args: list
    """

    with NetCom(args.HOSTNAME, args.USERNAME, args.TYPE, args.COMMANDS) as netcomm:
        netcomm


if __name__ == '__main__':
    main(parse_options())
