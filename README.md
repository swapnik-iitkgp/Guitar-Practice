# Guitar Practice App  

This project includes a **Guitar Practice** application and an **EXE generator** for converting the script into a standalone executable.  

## Files  
- **`guitar_practice.py`** - Main script for the Guitar Practice app.  
- **`exe_generator.py`** - Script to generate an executable using `PyInstaller`.  
- **`music_guitar.ico`** - Icon file for the application.  
- **`requirements.txt`** - List of dependencies needed to run the project.  

## Setup  
1. Install dependencies:  
   ```sh
   pip install -r requirements.txt
   ```  
2. Run the application:  
   ```sh
   python guitar_practice.py
   ```  

## Building the EXE  
To generate an executable using `exe_generator.py`, run:  
```sh
python exe_generator.py
```  

## Notes  
- Ensure you have `PyInstaller` installed before running the EXE generator:  
  ```sh
  pip install pyinstaller
  ```  
- The `music_guitar.ico` file is used as the app icon in the EXE build.  

Enjoy practicing your guitar! 🎸  
