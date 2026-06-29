import os
import shutil

base_dir = r"C:\JOB\AegisAI\data"
shoplifting_src_dir = os.path.join(base_dir, "Shoplifting")
csv_path = os.path.join(base_dir, "Labels", "Shoplifting.csv")

normal_dest_dir = os.path.join(base_dir, "Normal_Class")
crime_dest_dir = os.path.join(base_dir, "Shoplifting_Class")

os.makedirs(normal_dest_dir, exist_ok=True)
os.makedirs(crime_dest_dir, exist_ok=True)

print("Reading Shoplifting.csv raw lines...")

with open(csv_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

normal_count = 0
crime_count = 0

print("Scanning and sorting clips...")

# Loop through folders inside your Shoplifting directory
for folder in os.listdir(shoplifting_src_dir):
    folder_path = os.path.join(shoplifting_src_dir, folder)
    
    if os.path.isdir(folder_path):
        for clip in os.listdir(folder_path):
            if not clip.endswith(".mp4"):
                continue
                
            # Strip the '.mp4' extension to match the exact string format inside the CSV
            clip_name_without_ext = os.path.splitext(clip)[0]
            
            # Search for this clean clip name inside our CSV lines
            for line in lines:
                if clip_name_without_ext in line:
                    clean_line = line.strip()
                    label = clean_line[-1]  # Get the final character (0 or 1)
                    
                    src_file = os.path.join(folder_path, clip)
                    
                    if label == "0":
                        shutil.copy(src_file, os.path.join(normal_dest_dir, clip))
                        normal_count += 1
                    elif label == "1":
                        shutil.copy(src_file, os.path.join(crime_dest_dir, clip))
                        crime_count += 1
                    break  # Break inner loop, move to the next clip file

print("\n--- Sorting Complete! ---")
print(f"Total Normal clips copied: {normal_count}")
print(f"Total Shoplifting clips copied: {crime_count}")