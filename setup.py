import subprocess
import sys
import os
from pathlib import Path
import venv
import platform

def main():
    """
    Setup script for the report generator project.
    This script creates a virtual environment if needed, installs all dependencies
    from requirements.txt and sets up Playwright browsers.
    """
    print("Setting up the report generator project...")
    
    venv_dir = ".venv"
    venv_path = Path(venv_dir)
    
    # Check if virtual environment exists
    venv_exists = venv_path.exists()
    
    # Create virtual environment if it doesn't exist
    if not venv_exists:
        print(f"Creating virtual environment in {venv_dir}...")
        venv.create(venv_dir, with_pip=True)
        print(f"Virtual environment created at {venv_dir}")
    
    # Determine the path to the Python executable in the virtual environment
    if platform.system() == "Windows":
        venv_python = venv_path / "Scripts" / "python.exe"
        pip_cmd = venv_path / "Scripts" / "pip.exe"
    else:
        venv_python = venv_path / "bin" / "python"
        pip_cmd = venv_path / "bin" / "pip"
    
    if not venv_python.exists():
        print(f"Error: Could not find Python executable at {venv_python}")
        sys.exit(1)
    
    # Install requirements using the virtual environment's pip
    print(f"Installing dependencies from requirements.txt using {pip_cmd}...")
    result = subprocess.run([str(pip_cmd), "install", "-r", "requirements.txt"], check=False)
    
    if result.returncode != 0:
        print("Error installing dependencies. Please check your internet connection and try again.")
        sys.exit(1)
    
    # Install Playwright browsers using the virtual environment
    print("Installing Playwright browsers...")
    result = subprocess.run([str(venv_python), "-m", "playwright", "install"], check=False)
    
    if result.returncode == 0:
        print("\n" + "="*80)
        print("Setup completed successfully!")
        print("="*80)
        print("\nAll dependencies and browser components have been installed.")
        print(f"\nTo activate the virtual environment:")
        if platform.system() == "Windows":
            print(f"   .\\{venv_dir}\\Scripts\\activate")
        else:
            print(f"   source {venv_dir}/bin/activate")
        print("\nOnce activated, you can run the report generator with: python -m src.report_generator")
        print("\nThe report will be generated based on the configuration in config/default_config.yaml")
    else:
        print("\n" + "="*80)
        print("Setup encountered an error when installing Playwright browsers.")
        print("="*80)
        print("\nPlease try running the following command manually after activating the virtual environment:")
        print("   python -m playwright install")

if __name__ == "__main__":
    main() 