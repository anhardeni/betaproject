import sys
import os
sys.path.append(os.getcwd())
try:
    from frappe.utils import getdate
    
    test_str = "11-19-2015 00:00:00"
    print(f"Testing string: '{test_str}'")
    
    try:
        parsed = getdate(test_str)
        print(f"Result: {parsed} (Type: {type(parsed)})")
    except Exception as e:
        print(f"getdate FAILED: {e}")

    import dateutil.parser
    try:
        d = dateutil.parser.parse(test_str)
        print(f"dateutil found: {d}")
    except:
        print("dateutil failed")

except ImportError:
    print("Run this with bench python")
