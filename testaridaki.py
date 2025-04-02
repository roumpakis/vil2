from do_all import do_all
from Utils import Utils 
utils = Utils()

import os
import shutil
id_num = 795
do_all(id_num)
import os

# Βρίσκουμε το τρέχον directory
base_directory = os.getcwd()

print(f"Current directory: {base_directory}")
#base_directory = r"C:\Users\roub\Downloads\okok-master\okok-master"  # Βάλε το σωστό path εδώ
utils.setup_all_data_folder(base_directory)

all_data_path = os.path.join(base_directory,"static",  "all_data")
emsr_list = utils.find_unique_emsr(all_data_path)
print("Μοναδικά EMSR IDs:", emsr_list)