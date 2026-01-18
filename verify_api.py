import sys
import os

# Add apps directory to path so we can import singlecore_apps
sys.path.append(os.getcwd())

try:
    import singlecore_apps.api as api
    print("Successfully imported singlecore_apps.api")
    
    expected_functions = [
        "import_ceisa_excel",
        "get_ceisa_bc20_json", 
        "get_ceisa_bc27_json",
        "login_beacukai",
        "check_ceisa_status",
        "send_ceisa_document",
        "get_nested_data_all"
    ]
    
    missing = []
    for func in expected_functions:
        if hasattr(api, func):
            print(f"Found function: {func}")
        else:
            print(f"MISSING function: {func}")
            missing.append(func)
            
    if missing:
        print("FAILED: Some functions are missing from the API package.")
        sys.exit(1)
    else:
        print("SUCCESS: All expected functions are present.")
        sys.exit(0)

except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)
