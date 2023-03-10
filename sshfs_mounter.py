import os
import signal
import sys
import time
import subprocess
from pprint import pprint, pformat

poll_intervall = 2

def handle_exit(sig, frame):
    raise(KeyboardInterrupt)

def get_config_data(config_folder_path):
    import json

    # print ('reading config files from ' + config_folder_path)
    
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


def unmount(local_folder_path):
    try:
        cmd = 'umount "' + local_folder_path + '"'
        print ('trying to unmount "%s"' % local_folder_path)
        os.system(cmd)
    except Exception as e:
        print ('unable to unmount "%s": %s' % (local_folder_path, pformat(e)))
    try:
        cmd = 'rmdir "' + local_folder_path + '"'
        print ('removing directory "%s"' % local_folder_path)
        os.system(cmd)
    except Exception as e:
        print ('unable to remove "%s": %s' % (local_folder_path, pformat(e)))


if __name__ == "__main__":

    signal.signal(signal.SIGTERM, handle_exit)

    app_location = os.path.dirname(os.path.abspath(__file__))
    config_folder_path = os.path.join(app_location, 'config')
    local_folders = []
    local_locations = []

    try:
        while True:
            current_config = get_config_data(config_folder_path)
            locations = current_config.get('locations')
            if not isinstance(locations, list):
                print ('locations should be list but found %s' % type(locations))

            for location in locations:
                if not isinstance(location, dict):
                    print ('location should be a dictionary but found %s' % type(location))
                    pprint (location)
                    continue

                mount_options = location.get('mount_options')
                identity_file = location.get('identity_file')
                if mount_options and identity_file:
                    if "IdentityFile" not in mount_options:
                        mount_options += ',IdentityFile=' + identity_file
                remote_locations = location.get('remote_locations')
                if not remote_locations:
                    remote_locations = []
                elif isinstance(remote_locations, str):
                    remote_locations = [remote_locations]
                elif not isinstance(remote_locations, list):
                    print ('remote locations should be list but found %s' % type(location))
                    remote_locations = []

                remote_folders = {}
                for remote_location in remote_locations:
                    args = ['ssh']
                    if identity_file:
                        args.append('-i')
                        args.append(identity_file)
                    args.append(location.get('user@machine'))
                    args.append('ls -1 ' + remote_location)

                    p = subprocess.Popen(args, stdout=subprocess.PIPE)
                    output = p.communicate()[0].decode()

                    for line in output.splitlines():
                        if line in location.get('exclude_folders'):
                            continue
                        elif os.path.join(remote_location, line) in location.get('exclude_folders'):
                            continue
                        remote_folders[line] = remote_location

                local_locations = location.get('local_locations')
                if not local_locations:
                    local_locations = []
                elif isinstance(local_locations, str):
                    local_locations = [local_locations]
                elif not isinstance(local_locations, list):
                    print ('local locations should be list but found %s' % type(location))
                    remote_locations = []

                for local_location in local_locations:
                    local_folders = [x for x in os.listdir(local_location)]

                    for local_folder in local_folders:
                        if local_folder not in remote_folders.keys():
                            local_folder_path = os.path.join(local_location, local_folder)
                            unmount(local_folder_path)

                    for remote_folder in remote_folders.keys():
                        try:
                            cmd = 'mkdir -p "' + os.path.join(local_location, remote_folder) + '"'
                            os.system(cmd)
                            cmd = 'sshfs ' + location.get('user@machine') + ':"'
                            cmd += os.path.join(remote_folders.get(remote_folder), remote_folder) + '" '
                            cmd += '"' + os.path.join(local_location, remote_folder) + '" '
                            cmd += '-o ' + mount_options
                            cmd += ' 2>/dev/null'
                            os.system(cmd)
                        except:
                            pass
    except (KeyboardInterrupt, SystemExit):
        for local_location in local_locations:
            local_folders = [x for x in os.listdir(local_location)]

            for local_folder in local_folders:
                local_folder_path = os.path.join(local_location, local_folder)
                unmount(local_folder_path)
    except:
        pass

    finally:
        for local_location in local_locations:
            local_folders = [x for x in os.listdir(local_location)]

            for local_folder in local_folders:
                local_folder_path = os.path.join(local_location, local_folder)
                unmount(local_folder_path)

        time.sleep(poll_intervall)

