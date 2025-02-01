import os
import sys
import subprocess
import winshell
from win32com.client import Dispatch

def remove_obsolete_packages():
    """Remove obsolete packages incompatible with PyInstaller"""
    obsolete_packages = ['enum34', 'pathlib']
    for package in obsolete_packages:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', package], check=True)
            print(f"Removed {package} package")
        except subprocess.CalledProcessError:
            print(f"Could not remove {package}. Please remove manually.")

def create_exe():
    """Create executable for Guitar Practice"""
    script_path = 'guitar_practice.py'
    
    # Ensure script exists
    if not os.path.exists(script_path):
        print(f"Error: {script_path} not found!")
        return False
    
    # Construct PyInstaller command
    cmd = [
        'pyinstaller', 
        '--onefile', 
        '--windowed', 
        '--name', 'GuitarPractice',
        '--icon', os.path.join(os.getcwd(), 'music_guitar.ico'),
        script_path  # Remove the duplicate at the end
    ]
    
    # Run PyInstaller with detailed error handling
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("EXE created successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print("Error creating EXE:")
        print("Standard Output:", e.stdout)
        print("Standard Error:", e.stderr)
        return False

def create_shortcut():
    """Create desktop shortcut for the executable"""
    exe_path = os.path.join(os.getcwd(), 'dist', 'GuitarPractice.exe')
    
    if not os.path.exists(exe_path):
        print(f"Executable not found at {exe_path}")
        return False
    
    desktop = winshell.desktop()
    shortcut_path = os.path.join(desktop, 'Guitar Practice.lnk')
    
    try:
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = exe_path
        shortcut.WorkingDirectory = os.path.dirname(exe_path)
        shortcut.IconLocation = exe_path
        shortcut.save()
        print("Shortcut created successfully!")
        return True
    except Exception as e:
        print(f"Error creating shortcut: {e}")
        return False

def main():
    remove_obsolete_packages()
    
    if create_exe():
        create_shortcut()
    else:
        print("Failed to create executable. Check the error messages above.")

if __name__ == '__main__':
    main()