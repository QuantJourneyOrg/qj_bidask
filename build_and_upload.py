#!/usr/bin/env python3
"""
Build and upload script for quantjourney-bidask package.

This script automates the process of building and uploading the package to PyPI.
Run this script after ensuring all version numbers are updated.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def clean_build_artifacts():
    """Clean previous build artifacts."""
    print("\n🧹 Cleaning build artifacts...")
    
    # Directories to clean
    clean_dirs = ['build', 'dist', '*.egg-info']
    
    for pattern in clean_dirs:
        if '*' in pattern:
            # Handle glob patterns
            for path in Path('.').glob(pattern):
                if path.is_dir():
                    print(f"  Removing {path}")
                    shutil.rmtree(path)
        else:
            # Handle exact directory names
            if os.path.exists(pattern):
                print(f"  Removing {pattern}")
                shutil.rmtree(pattern)
    
    print("✅ Build artifacts cleaned")

def check_requirements():
    """Check if required tools are installed."""
    print("\n🔍 Checking requirements...")
    
    required_tools = ['twine', 'build']
    missing_tools = []
    
    for tool in required_tools:
        result = subprocess.run(f"python -m {tool} --version", shell=True, capture_output=True)
        if result.returncode != 0:
            missing_tools.append(tool)
        else:
            print(f"  ✅ {tool} is available")
    
    if missing_tools:
        print(f"\n❌ Missing required tools: {', '.join(missing_tools)}")
        print("Install them with:")
        for tool in missing_tools:
            print(f"  pip install {tool}")
        return False
    
    print("✅ All required tools are available")
    return True

def validate_package():
    """Validate package configuration."""
    print("\n🔍 Validating package configuration...")
    
    # Check if essential files exist
    essential_files = [
        'pyproject.toml',
        'README.md',
        'LICENSE',
        'quantjourney_bidask/__init__.py',
        'quantjourney_bidask/_version.py'
    ]
    
    for file_path in essential_files:
        if not os.path.exists(file_path):
            print(f"❌ Missing essential file: {file_path}")
            return False
        else:
            print(f"  ✅ {file_path}")
    
    # Try to import the package to check for syntax errors
    try:
        sys.path.insert(0, '.')
        import quantjourney_bidask
        print(f"  ✅ Package imports successfully (version: {quantjourney_bidask.__version__})")
    except Exception as e:
        print(f"❌ Package import failed: {e}")
        return False
    
    print("✅ Package validation passed")
    return True

def build_package():
    """Build the package."""
    return run_command("python -m build", "Building package")

def check_package():
    """Check the built package with twine."""
    return run_command("python -m twine check dist/*", "Checking package")

def upload_to_test_pypi():
    """Upload to Test PyPI."""
    print("\n🚀 Uploading to Test PyPI...")
    print("You'll be prompted for your Test PyPI credentials.")
    return run_command(
        "python -m twine upload --repository testpypi dist/*",
        "Uploading to Test PyPI"
    )

def upload_to_pypi():
    """Upload to PyPI."""
    print("\n🚀 Uploading to PyPI...")
    print("You'll be prompted for your PyPI credentials.")
    return run_command(
        "python -m twine upload dist/*",
        "Uploading to PyPI"
    )

def main():
    """Main build and upload process."""
    print("🏗️  QuantJourney Bid-Ask Spread Estimator - Build & Upload")
    print("=" * 60)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Step 1: Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Step 2: Validate package
    if not validate_package():
        sys.exit(1)
    
    # Step 3: Clean artifacts
    clean_build_artifacts()
    
    # Step 4: Build package
    if not build_package():
        sys.exit(1)
    
    # Step 5: Check package
    if not check_package():
        sys.exit(1)
    
    # Step 6: Ask user what to do
    print("\n🎯 Package built successfully!")
    print("What would you like to do next?")
    print("1. Upload to Test PyPI (recommended first)")
    print("2. Upload to PyPI (production)")
    print("3. Exit (just build)")
    
    choice = input("\nEnter your choice (1/2/3): ").strip()
    
    if choice == "1":
        if upload_to_test_pypi():
            print("\n✅ Successfully uploaded to Test PyPI!")
            print("Test your package with:")
            print("pip install --index-url https://test.pypi.org/simple/ quantjourney-bidask")
    elif choice == "2":
        confirm = input("\n⚠️  Are you sure you want to upload to production PyPI? (yes/no): ").strip().lower()
        if confirm == "yes":
            if upload_to_pypi():
                print("\n🎉 Successfully uploaded to PyPI!")
                print("Your package is now available:")
                print("pip install quantjourney-bidask")
        else:
            print("Upload cancelled.")
    elif choice == "3":
        print("Build completed. Upload skipped.")
    else:
        print("Invalid choice. Exiting.")
    
    print("\n📦 Build process completed!")

if __name__ == "__main__":
    main()