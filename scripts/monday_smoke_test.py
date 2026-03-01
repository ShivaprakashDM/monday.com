import os

def run_smoke_test():
    print("Running Monday.com smoke test...")
    if not os.environ.get("MONDAY_API_KEY"):
        print("Warning: MONDAY_API_KEY environment variable not set.")
    else:
        print("MONDAY_API_KEY is found.")
    print("Smoke test completed.")

if __name__ == "__main__":
    run_smoke_test()
