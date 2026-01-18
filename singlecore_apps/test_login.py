import frappe
from singlecore_apps.api import login_beacukai
import sys

def test_login(username, password):
    print(f"Testing login for user: {username}")
    try:
        result = login_beacukai(username, password)
        print("Result:", result)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: bench execute singlecore_apps.test_login.test_login --args 'username,password'")
    else:
        test_login(sys.argv[1], sys.argv[2])
