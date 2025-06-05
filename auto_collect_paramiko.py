import os
import paramiko
import pathlib
from scp import SCPClient
import json

import numpy as np
from nexcsi import decoder
import matplotlib
import matplotlib.pyplot as plt
import time
from pcap_to_image_test import pcap_to_image

#home_router = "20:4e:f6:c1:ce:57"






def setup_monitor(SSH:paramiko.SSHClient, ch, bw, ns, mac=None):
    #b64_params = SSH.exec_command(f'mcp -C 1 -N {ns} -c {ch}/{bw} -m {mac}')[1].readlines()[0].replace("\n", "")
    cores = '-C 1'
    spatial_stream = f'-N {ns}'
    channel_bandwidth = f'-c {ch}/{bw}'
    mac_filtering = '' if mac==None else f' -m {mac}'
    
    params = [cores, spatial_stream, channel_bandwidth, mac_filtering]
    print(params)

    SSH.exec_command('sudo ifconfig wlan0 up')
    SSH.exec_command(f'nexutil -Iwlan0 -s500 -b -l34 -v$(mcp {" ".join(params)})')
    SSH.exec_command('sudo iw dev wlan0 interface add mon0 type monitor')
    SSH.exec_command('sudo ip link set mon0 up')



with open('collection_params.json') as f:
    collection_params = json.load(f)

if input('change parameters [y/N]? ') in ['y', 'Y']:
    for key in collection_params.keys():
        new_param = input(f'{key}? [{collection_params[key]}]')
        if not new_param=='':
            collection_params[key] = new_param

with open('collection_params.json', 'w') as f:
    json.dump(collection_params, f)



ssh = paramiko.SSHClient()

ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

ssh.connect(collection_params['rpi_address']+"%"+collection_params['interface_id'],
            port=22,
            username='pi',
            password='raspberry',
            timeout=3)



# sync raspberry pis to standard time
ssh.exec_command(f'sudo date -s @{time.time()}')

# setup wifi interface monitor on rpi
if collection_params['enable_mac_filtering']=='0':
    setup_monitor(ssh, 
                  collection_params['channel'], 
                  collection_params['bandwidth'], 
                  collection_params['n_streams'])
else:
    setup_monitor(ssh, 
                  collection_params['channel'], 
                  collection_params['bandwidth'], 
                  collection_params['n_streams'],
                  collection_params['mac_address'])


# find current working directory (cwd) and define file_path: the place where all files will be saved
cwd = pathlib.Path.cwd()
data_path = cwd / 'data' / f"{collection_params['channel']}_{collection_params['bandwidth']}" / 'Two_Pis'

# creates file_path from current working directory if it doesn't exist
data_path.mkdir(parents=True, exist_ok=True)


print('current directory:', data_path.as_posix())




# scan current directory for past data
p = pathlib.Path(data_path).glob('**/*.pcap')
files = [x.name for x in p]

acts = {}
act = ""

for filename in files:
    # this removes the extension (.pcap) from the filename and splits the action name and number of the file
    # all files are saved as 'action-1.pcap', 'other_action-31.pcap', etc...
    action, number = filename.rsplit('.',1)[0].rsplit('-', 1)
    if not action in acts.keys():
        acts[action] = [0]
    else:
        acts[action] += [int(number)]




# displays previous actions and how many there are of each
if not len(acts.keys()) == 0:
    print("previous actions in this directory:")
    max_filename_length = max([len(key) for key in acts.keys()])
    for item in acts.items():
        print(item[0].rjust(max_filename_length) + f'\t [{len(item[1])} time{"" if len(item[1])==0 else "s"}]')
else:
    print("empty directory")





# DATA COLLECTION

# the 'time or packets' parameter decides whether to stop after a certain number of packets or seconds
stop_condition = f"-c {collection_params['n_packets']}" if collection_params['time_or_packets (0/1)']=="1"\
                                                        else f"-G {collection_params['time']} -W 1"


new_act = input('\nactivity (q to quit)? ')
while not new_act=='q':
    # leave action unchanged if nothing is entered as input
    act = act if new_act=="" else new_act
    
    # increment counter for corresponding action
    if act not in acts.keys():
        acts[act] = [0]
    else:  
        #print(acts)
        acts[act] += [max(acts[act])+1]

    new_filename = act + '-' + str(max(acts[act]))
    print(f'recording {new_filename}.pcap')

    # these lines of code do the following:
    #    run the data collection and save to a temporary file
    #    copy the .pcap file to directory on host computer
    #    remove .pcap file from raspberry pi

    #print(stop_condition)

    stdin, stdout, stderr = ssh.exec_command(f'sudo tcpdump -i wlan0 dst port 5500 -vv -w {new_filename}.pcap ' + stop_condition)
    exit_status = stdout.channel.recv_exit_status()
    
    # a sanitizer function is necessary to allow wildcards (*) in filenames
    with SCPClient(ssh.get_transport(), sanitize=lambda x: x) as scp:
        print(exit_status)
        scp.get(f'*.pcap', data_path.as_posix())

    ssh.exec_command(f'rm ~/*.pcap')
    
    new_act = input('\nactivity (q to quit)? ')



# turn all pcap files to images and move resulting images to images folder
# for file in list(data_path.glob("*.pcap")):
#    pcap_to_image(file, rmax=2000, is_fig=False, use_time=True, pixels_per_second=500)

#for image in list(data_path.glob("*.png")):
#    image.rename(image_path / image.name)
