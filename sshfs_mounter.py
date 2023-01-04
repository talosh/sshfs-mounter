import os
import sys
import time
import subprocess
from pprint import pprint, pformat

poll_intervall = 2

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
    locations = current_config.get('locations')
    if not isinstance(locations, list):
        locations = []
        mount_options = ""

    while True:
        for location in locations:
            args = ['ssh']
            args.append(location.get('user@machine'))
            args.append('ls -1 ' + location.get('remote_folder'))

            pprint (args)
            sys.exit()

            p = subprocess.Popen(args, stdout=subprocess.PIPE)
            output = p.communicate()[0]
            remote_folders = []
            for line in output.splitlines():
                if line in location.get('exclude_folders'):
                    continue
                remote_folders.append(line)
            local_folders = [x for x in os.listdir(location.get('local_folder'))]

            pprint (local_folders)

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

