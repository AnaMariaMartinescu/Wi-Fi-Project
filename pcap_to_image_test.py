from scipy.interpolate import interp1d
from nexcsi import decoder
import pathlib
import matplotlib
import matplotlib.pyplot as plt
import numpy as np



def pcap_to_image(file_path: pathlib.Path, rmax=2000, is_fig: bool = False, use_time:bool=True, pixels_per_second=500):
    device = "raspberrypi"
    samples = decoder(device).read_pcap(file_path.as_posix())
    timestamps = np.array(samples['ts_sec'] + samples['ts_usec'] / 1e6)
    csi = decoder(device).unpack(samples['csi'], zero_nulls=True, zero_pilots=True)

    h, w = csi.shape
    rgb = colormap(csi, rmax)

    # dpi: dots per inch. Since figsize is later given in inches,
    # this gives us a way to control output image size. For some obscure reason,
    # some scaling needs to be done to actually get the desired image size. 
    # Changing the dpi doesn't actually change anything to the output image,
    # a low value just causes some overflow in intermediate steps 
    dpi = 100

    img_w = w / dpi

    if use_time:
        time_min, time_max = timestamps[0], timestamps[-1]
        resolution = int((time_max - time_min)*pixels_per_second)
        img_h = resolution / dpi

        # ChatGPT wrote this, but it essentially just interpolates the (non-uniform) data to a uniform grid
        uniform_timestamps = np.linspace(time_min, time_max, resolution)
        
        img_rgb = interp_to_grid(rgb, timestamps, uniform_timestamps, resolution)

    else:
        img_h = h / dpi
        img_rgb = rgb



    plt.figure(figsize=(img_w, img_h))
    plt.imshow(img_rgb)

    if not is_fig:
        plt.axis('off')
        plt.gca().xaxis.set_major_locator(matplotlib.ticker.NullLocator())
        plt.gca().yaxis.set_major_locator(matplotlib.ticker.NullLocator())
    else:
        plt.colorbar()
        # to be fixed, doesn't really work
        plt.rcParams['xtick.bottom'] = False
        plt.rcParams['xtick.labelbottom'] = False
        plt.rcParams['xtick.top'] = True
        plt.rcParams['xtick.labeltop'] = True



    # for some reason, the dpi needs to be scaled by 256/197 for stuff to work
    # might be due to some unit conversion (not cm to inch though, 1 in = 2.54cm, 
    # which is off by a factor of about 2) 
    plt.savefig(file_path.as_posix().rsplit('.', 1)[0] + '.png',
                pad_inches=0, bbox_inches='tight', dpi=dpi/197*256)
    print('turned', file_path.name, 'into an image')

def old_pcap_to_image(file_path: pathlib.Path):
    device = "raspberrypi" # nexus5, nexus6p, rtac86u

    samples = decoder(device).read_pcap(file_path.as_posix())

    #plt.hist(np.diff(samples['ts_sec'] + samples['ts_usec']/1e6), bins=100)
    #plt.show()

    # Accessing CSI as type complex64
    csi = decoder(device).unpack(samples['csi'], zero_nulls=True, zero_pilots=True)

    plt.figure(figsize=(csi.shape[0]/csi.shape[1],1))
    print((1,csi.shape[0]/csi.shape[1]))
    print(csi.shape)
    plt.imshow(abs(csi.T), cmap='viridis', interpolation='nearest', vmax=1000)
    plt.axis('off')
    plt.gca().xaxis.set_major_locator(matplotlib.ticker.NullLocator())
    plt.gca().yaxis.set_major_locator(matplotlib.ticker.NullLocator())
    plt.savefig(file_path.as_posix().rsplit('.',1)[0] + '.png', pad_inches=0, bbox_inches='tight', transparent=True, dpi=100)

def pcaps_to_image(file_paths, rmax=2000, is_fig=False, pixels_per_second=500):
    device = "raspberrypi"

    all_samples = np.array([decoder(device).read_pcap(file_path.as_posix()) for file_path in file_paths])
    all_timestamps = np.array([np.array(samples['ts_sec'] + samples['ts_usec'] / 1e6) for samples in all_samples])
    all_csi = np.array([decoder(device).unpack(samples['csi'], zero_nulls=True, zero_pilots=True) for samples in all_samples])

    lengths = np.apply_along_axis(len, 1, all_csi)
    n_subs = np.apply_along_axis(len, 2, all_csi)

    n, lengths, n_subs = all_csi.shape
    print(all_csi.shape)


    rgbs = np.array([colormap(csi, rmax) for csi in all_csi])

    # dpi: dots per inch. Since figsize is later given in inches,
    # this gives us a way to control output image size. For some obscure reason,
    # some scaling needs to be done to actually get the desired image size. 
    # Changing the dpi doesn't actually change anything to the output image,
    # a low value just causes some overflow in intermediate steps 
    dpi = 100

    print(n_subs)
    img_w = np.sum(n_subs) / dpi

    # print(all_timestamps.shape)
    #print(all_timestamps[:,0])
    time_min = max(all_timestamps[:, 0])
    time_max = min(all_timestamps[:, -1])

    if time_max < time_min:
        # print(all_timestamps[:, 0])
        # print(all_timestamps[:, -1])
        print(', '.join([file_path.name for file_path in file_paths[:-1]]), 'and', file_paths[-1].name)
        print("recordings do not overlap")
        return
    
    resolution = int((time_max - time_min)*pixels_per_second)
    img_h = resolution / dpi

    # ChatGPT wrote this, but it essentially just interpolates the (non-uniform) data to a uniform grid
    uniform_timestamps = np.linspace(time_min, time_max, resolution)
    #print('hello', rgbs.shape)
    img_rgbs = [interp_to_grid(rgbs[i], y=all_timestamps[i], y_uni=uniform_timestamps, res=resolution) for i in range(len(file_paths))]

    img = np.concatenate(img_rgbs, axis=1)
    print(img.shape)


    plt.figure(figsize=(img_w, img_h))
    plt.imshow(img)

    if not is_fig:
        plt.axis('off')
        plt.gca().xaxis.set_major_locator(matplotlib.ticker.NullLocator())
        plt.gca().yaxis.set_major_locator(matplotlib.ticker.NullLocator())
    else:
        plt.colorbar()
        # to be fixed, doesn't really work
        plt.rcParams['xtick.bottom'] = False
        plt.rcParams['xtick.labelbottom'] = False
        plt.rcParams['xtick.top'] = True
        plt.rcParams['xtick.labeltop'] = True



    # for some reason, the dpi needs to be scaled by 256/197 for stuff to work
    # might be due to some unit conversion (not cm to inch though, 1 in = 2.54cm, 
    # which is off by a factor of about 2) 
    plt.savefig(file_paths[0].as_posix().rsplit('.', 1)[0] + '_combined.png',
                pad_inches=0, bbox_inches='tight', dpi=dpi*512/198.25)
    print('turned', ', '.join([file_path.name for file_path in file_paths[:-1]]), 'and', file_paths[-1].name, 'into an image')
    plt.close()



def colormap(z, rmax):
    amp = np.abs(z)
    phase = np.angle(z)

    # Red: csi amplitude
    # Green, Blue: csi phase (use 2 channels to avoid
    # false discontinuities between -pi and pi)
    R = np.clip(amp / rmax, 0, 1)
    G = (np.sin(phase))/2 + 1/2
    B = (np.cos(phase))/2 + 1/2

    return np.stack((R, G, B), axis=-1)


def interp_to_grid(data, y, y_uni, res):
    print(data.shape)
    _, w, d = data.shape
    interp_data = np.zeros((res, w, d), dtype=np.float32)
    for channel in range(d):
        interp = interp1d(y, data[:, :, channel], axis=0, bounds_error=False, fill_value=0, kind='nearest')
        interp_data[:, :, channel] = interp(y_uni)
    return interp_data



"""
data_path = pathlib.Path.cwd() / 'data' / '44_80' / 'TwoRPI_test'
files = list(data_path.glob("*.pcap"))

for file in files:
    pcap_to_image(file, rmax=2000, is_fig=False, use_time=True)

"""