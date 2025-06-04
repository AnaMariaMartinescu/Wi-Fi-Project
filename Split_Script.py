
import os
import shutil
import random
from tqdm import tqdm

#Make sure you make the folowing empty folder 
#Data_Split/
    #├── Training_Data/
    #├── Validation_Data/
    #├── Test_Data/


source_dir = 'C:/Users/Agent47/Desktop/Wi-fi Project/Body_Movements_Train'  # all images sorted in class folders
target_base = 'C:/Users/Agent47/Desktop/Wi-fi Project/Data_Split' #This is the new empty folder

splits = {
    'Training_Data': 0.8,
    'Validation_Data': 0.1,
    'Test_Data': 0.1
}

random.seed(42)

for split_name, split_ratio in splits.items():
    for class_name in os.listdir(source_dir):
        src_class_dir = os.path.join(source_dir, class_name)
        dst_class_dir = os.path.join(target_base, split_name, class_name)
        os.makedirs(dst_class_dir, exist_ok=True)

        all_files = [f for f in os.listdir(src_class_dir) if f.endswith(".png")]
        random.shuffle(all_files)

        split_count = int(len(all_files) * split_ratio)
        split_files = all_files[:split_count]
        # Remove used files from the pool
        all_files = all_files[split_count:]

        for f in tqdm(split_files, desc=f"Copying {split_name}/{class_name}"):
            shutil.copy(os.path.join(src_class_dir, f), os.path.join(dst_class_dir, f))

        # Update the source directory so next split gets correct pool
        source_dir = 'C:/Users/Agent47/Desktop/Wi-fi Project/Body_Movements_Train' #make sure is the path to the folder that contains the data (not the empty one)
