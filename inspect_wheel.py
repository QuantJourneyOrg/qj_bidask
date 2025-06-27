import zipfile
import os

def inspect_wheel_metadata(wheel_path):
    """
    Extracts and prints the METADATA file from a Python wheel (.whl) file.

    Args:
        wheel_path (str): The full path to the .whl file.
    """
    if not os.path.exists(wheel_path):
        print(f"Error: Wheel file not found at '{wheel_path}'")
        return

    try:
        with zipfile.ZipFile(wheel_path, 'r') as wheel_zip:
            # Find the METADATA file; it's usually in the .dist-info directory
            metadata_file_name = None
            for name in wheel_zip.namelist():
                if name.endswith('.dist-info/METADATA'):
                    metadata_file_name = name
                    break

            if metadata_file_name:
                print(f"--- Contents of {metadata_file_name} ---")
                with wheel_zip.open(metadata_file_name) as metadata_file:
                    content = metadata_file.read().decode('utf-8')
                    print(content)
                print("--- End of METADATA ---")
            else:
                print(f"Error: METADATA file not found inside '{wheel_path}'")

    except zipfile.BadZipFile:
        print(f"Error: '{wheel_path}' is not a valid zip file (or a corrupted wheel).")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# IMPORTANT: Replace 'path/to/your/quantjourney_bidask-0.9.0-py3-none-any.whl'
# with the actual path to your generated wheel file.
# You can find it in your 'dist/' directory after running 'python -m build'.
if __name__ == "__main__":
    # Example usage:
    # Assuming your wheel is in the 'dist' directory and named 'quantjourney_bidask-0.9.0-py3-none-any.whl'
    # You might need to adjust the path based on your actual file name and location.
    # A simple way to get the latest wheel:
    # import glob
    # wheel_files = glob.glob('dist/*.whl')
    # if wheel_files:
    #     latest_wheel = max(wheel_files, key=os.path.getctime)
    #     print(f"Found latest wheel: {latest_wheel}")
    #     inspect_wheel_metadata(latest_wheel)
    # else:
    #     print("No wheel files found in 'dist/' directory.")

    # For direct use, replace with your exact wheel path:
    wheel_file_path = "dist/quantjourney_bidask-0.9.0-py3-none-any.whl"
    inspect_wheel_metadata(wheel_file_path)

