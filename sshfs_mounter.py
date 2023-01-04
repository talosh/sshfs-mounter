#!/usr/bin/python

import os
import sys
import time
import subprocess
from pprint import pprint, pformat

poll_intervall = 2
locations = [
    {
        'user@host': 'dladmin@10.1.15.30',
        'remote_folder': '/Volumes/',
        'local_folder': '/mnt/readonly/nicki/',
        'exclude_folders': [
            'G-UTILITIES',
            'mnt',
            'Macintosh HD',
            'Recovery',
            'beyonce',
            'dl-tests',
            'images1',
            'images1-1',     
            'minaj'
        ]
    }
]

mount_options = 'ro,reconnect,ServerAliveInterval=15,ServerAliveCountMax=3,uid=506,gid=506,allow_other,IdentityFile=/etc/ssh/ssh_host_rsa_key'

def get_config_data(config_folder_path):
    import json

    print ('reading config files from ' + config_folder_path)
    
    data = dict()
    data['config_folder_path'] = config_folder_path
    
    if not os.path.isdir(config_folder_path):
        return data
    
    config_files = os.listdir(config_folder_path)
    if not config_files:
        return data
    
    for config_file_name in config_files:
        if not config_file_name.endswith('.json'):
            continue
        config_file_path = os.path.join(
            config_folder_path,
            config_file_name
        )

        try:
            with open(config_file_path, 'r') as config_file:
                config = json.load(config_file)
                config_file.close()
        except Exception as e:
            print('[WARNING] Unable to read config file %s' % config_file_path)
            print(e)

        name, ext = os.path.splitext(config_file_name)
        data[name] = config

    return data


if __name__ == "__main__":

    app_location = os.path.dirname(os.path.abspath(__file__))
    config_folder_path = os.path.join(app_location, 'config')
    current_config = get_config_data(config_folder_path)
    pprint (current_config)
    sys.exit()

    while True:
        for location in locations:
            args = ['ssh']
            args.append(location.get('user@host'))
            args.append('ls -1 ' + location.get('remote_folder'))
            p = subprocess.Popen(args, stdout=subprocess.PIPE)
            output = p.communicate()[0]
            remote_folders = []
            for line in output.splitlines():
                if line in location.get('exclude_folders'):
                    continue
                remote_folders.append(line)
            local_folders = [x for x in os.listdir(location.get('local_folder'))]
            for local_folder in local_folders:
                if local_folder not in remote_folders:
                    try:
                        local_folder_path = os.path.join(location.get('local_folder'), local_folder)
                        cmd = 'sudo umount "' + local_folder_path + '"; sudo rmdir "' + local_folder_path + '"'
                        os.system(cmd)
                    except:
                        pass

            for remote_folder in remote_folders:
                try:
                    cmd = 'sudo mkdir -p "' + os.path.join(location.get('local_folder'), remote_folder) + '"'
                    os.system(cmd)
                    cmd = 'sudo sshfs ' + location.get('user@host') + ':"'
                    cmd += os.path.join(location.get('remote_folder'), remote_folder) + '" '
                    cmd += '"' + os.path.join(location.get('local_folder'), remote_folder) + '" '
                    cmd += '-o ' + mount_options
                    cmd += ' 2>/dev/null'
                    os.system(cmd)
                except:
                    pass

        time.sleep(poll_intervall)

