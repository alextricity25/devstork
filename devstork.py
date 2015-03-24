import itertools
import novaclient.exceptions
import os
import paramiko
import pprint
import socket
import sys
import time
import yaml

from novaclient.v1_1 import client

from config import get_config
from parser import get_parser


class Devstork(object):

    def __init__(self, config):
        """
        Inits the Devstork instance.
        Saves the configuration and creates a novaclient instance.

        @param config - Dictionary

        """
        self._config = config
        self._client = client.Client(**self._config.get('auth', {}))

    def _create_start(self):
        """
        Signals that creation has started.
        Saves the current time for use with timeout checks.

        """
        self._create_started = time.time()

    def _check_create_time(self):
        """
        Checks the current time against the creation time + the timeout.
        Raises an exception if the current time has exceeded the timeout.

        """
        # Deletes will not have a create started timestamp
        if not hasattr(self, '_create_started'):
            return True

        timeout = self._config['create_timeout']
        if timeout > 0 and time.time() > self._create_started + timeout:
                raise Exception(
                    "VM Creation timed out. Took longer than %s seconds"
                    % timeout
                )

    def get_server(self):
        """
        Uses the nova client to query for a server.
        Uses the uuid saved in the file specified by the config.

        @returns Server|None

        """
        if os.path.isfile(self._config['id_file']):
            with open(self._config['id_file']) as f:
                data = yaml.safe_load(f)
            try:
                server = self._client.servers.get(data['id'])
                return server
            except novaclient.exceptions.NotFound:
                pass
        return None

    def get_userdata(self):
        """
        Returns the contents of the userdata file specified by the config.

        @returns String

        """
        userdata = None
        with open(self._config['userdata_file'], 'r') as f:
            userdata = f.read()
        return userdata

    def save_server(self, server):
        """
        Saves the server information to disk.

        @param server - Novaclient server instance

        """
        with open(conf['id_file'], 'w') as f:
            yaml.safe_dump({
                'id': server.id,
                'networks': server.networks,
                'name': server.name
            }, f)

    def wait_for_status(self,
                        target_status,
                        fail_on_error=True,
                        fail_on_not_exist=True):
        """
        Waits for the server to have the target status.

        @param target_status - String target_status
        @param fail_on_error - Boolean fail_on_error - Fail if error status
        @param fail_on_not_exist - Fail if the server no longer exists.
        @return Boolean

        """
        print "Waiting for server status..."
        # Set initial status to force the first status change
        status = ''

        while not (status.lower() == target_status.lower()):
            self._check_create_time()
            server = self.get_server()
            if server:
                # Check for status update
                if not (server.status.lower() == status.lower()):
                    status = server.status
                    print "Server status: %s" % status

                if status.lower() == target_status.lower():
                    return True

                if status.lower() == 'error' and fail_on_error:
                    return True
            # Nothing returned. Server does not exist
            else:
                print "Server does not exist"
                return not fail_on_not_exist
            time.sleep(10)

        # Met the condition of while loop. target status must have been met.
        return True

    def wait_for_userdata_status(self, server):
        """
        Waits for the userdata status on the vm. This implies that the
        userdata script itself has some sort of signalling mechanism.
        To be used with this tool, the userdata script should write to a file
        with the current status.  When that file contains the end status,
        this tool will view the vm as completed.

        This tool ssh's into the created vm and repeatedly check the userdata
        status file.

        @param server - Novaclient server instance

        """
        print "Waiting for userdata..."
        target_status = "finished"
        status = ''

        ssh_host = server.networks['public'][0]
        ssh_user = self._config['ssh_user']
        ssh_timeout = self._config['ssh_timeout']
        ssh_keyfile = self._config['ssh_keyfile']
        end_status = self._config['userdata_end_status']
        status_file = self._config['userdata_status_file']
        ssh_command = "cat '%s'" % status_file

        while not (status.lower() == end_status.lower()):
            self._check_create_time()
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ssh_host, username='root',
                            timeout=10, key_filename=ssh_keyfile)
                stdin, stdout, stderr = ssh.exec_command(ssh_command)
                new_status = stdout.read().rstrip()
                ssh.close()
                if new_status != status:
                    print "Userdata status: %s" % status
                    status = new_status
                if status.lower() == end_status.lower():
                    return True
            except socket.timeout as e:
                # SSHD isnt always immediately available on the vm
                pass
            except socket.error as e:
                # SSHD isnt always immediately available on the vm
                pass
            time.sleep(10)
        return False

    def create(self, wait_for_userdata=False):
        """
        Creates the server if it doesn't already exist.
        If a server is created, it's uuid is saved to a file so that
        it can be deleted easily later.

        @params args - Args created by ArgParser

        """
        self._create_start()
        server = self.get_server()
        if server:
            print "Server already exists:"
        else:
            print "Creating a new instance:"
            kwargs = {'key_name': self._config['key_name']}

            # Add userdata
            userdata = self.get_userdata()
            if userdata:
                print "Adding userdata"
                kwargs['userdata'] = userdata

            server = self._client.servers.create(conf['name'],
                                                 conf['image'],
                                                 conf['flavor'],
                                                 **kwargs)

        # Store server id to indicate server has been created
        self.save_server(server)
        self.wait_for_status('active')
        self._check_create_time()

        # Update server with network information and save again
        server = self.get_server()
        self.save_server(server)

        if wait_for_userdata:
            self.wait_for_userdata_status(server)

        print "Server name: ", server.name
        print "Server id: ", server.id
        print "Networks: ", server.networks

    def delete(self):
        """
        Deletes the server if the file already exists.

        """
        server = self.get_server()
        if server:
            server.delete()
            print "Deleting server %s" % server.name
            self.wait_for_status('deleted', fail_on_not_exist=False)
            os.remove(self._config['id_file'])
        else:
            print "Nothing to delete."

if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()
    conf = get_config(args)

    d = Devstork(conf)
    # Run the subcommand - either create or delete
    if args.action == 'create':
        d.create(wait_for_userdata=args.wait_for_userdata)
    elif args.action == 'delete':
        d.delete()
