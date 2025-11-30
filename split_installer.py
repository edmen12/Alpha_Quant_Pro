import os

CHUNK_SIZE = 1900 * 1024 * 1024  # 1.9 GB (Safe margin for 2GB limit)
INSTALLER_DIR = "Installer"
SOURCE_FILE = os.path.join(INSTALLER_DIR, "AlphaQuantPro_Setup.exe")

def split_file():
    if not os.path.exists(SOURCE_FILE):
        print(f"Error: {SOURCE_FILE} not found.")
        return

    file_size = os.path.getsize(SOURCE_FILE)
    print(f"Original File Size: {file_size / (1024*1024*1024):.2f} GB")
    
    with open(SOURCE_FILE, 'rb') as src:
        part_num = 1
        while True:
            chunk = src.read(CHUNK_SIZE)
            if not chunk:
                break
            
            part_name = f"AlphaQuantPro_Setup.part{part_num}"
            part_path = os.path.join(INSTALLER_DIR, part_name)
            
            with open(part_path, 'wb') as dst:
                dst.write(chunk)
            
            print(f"Created: {part_name} ({len(chunk) / (1024*1024):.2f} MB)")
            part_num += 1

    print("\n✅ Split Complete!")
    print("Files to upload to GitHub:")
    for i in range(1, part_num):
        print(f"  - AlphaQuantPro_Setup.part{i}")

    # Create Merge Script
    bat_content = "@echo off\n"
    bat_content += "echo Merging installer parts...\n"
    bat_content += "copy /b AlphaQuantPro_Setup.part1 + AlphaQuantPro_Setup.part2 AlphaQuantPro_Setup.exe\n"
    bat_content += "echo.\n"
    bat_content += "echo ✅ Merge complete! You can now run AlphaQuantPro_Setup.exe\n"
    bat_content += "pause\n"

    bat_path = os.path.join(INSTALLER_DIR, "MERGE_INSTALLER.bat")
    with open(bat_path, "w") as f:
        f.write(bat_content)
    print(f"Created Merge Script: {bat_path}")

if __name__ == "__main__":
    split_file()
