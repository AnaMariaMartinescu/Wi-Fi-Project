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
    amplitude = np.abs(csi)
    phase = np.angle(csi)

    # Red: csi amplitude
    # Green, Blue: csi phase (use 2 channels to avoid
    # false discontinuities between -pi and pi)
    R = np.clip(amplitude / rmax, 0, 1)
    G = (np.sin(phase))/2 + 1/2
    B = (np.cos(phase))/2 + 1/2

    plt.hist(amplitude.flatten(), 256, density=True, color='green', alpha=0.7)
    #print(max(amplitude.flatten()), np.mean(amplitude.flatten()))

    rgb = np.stack((R, G, B), axis=-1)


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
        img_rgb = np.zeros((resolution, w, 3), dtype=np.float32)
        for channel in range(3):
            interp = interp1d(timestamps, rgb[:, :, channel], axis=0, bounds_error=False, fill_value=0, kind='nearest')
            img_rgb[:, :, channel] = interp(uniform_timestamps)

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


"""
data_path = pathlib.Path.cwd() / 'test_data'
files = list(data_path.glob("*.pcap"))

for file in files:
    pcap_to_image(file, rmax=2000, is_fig=False, use_time=True)

"""