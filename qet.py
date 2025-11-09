### **`qet` (Main Executable)**

```python
#!/usr/bin/env python3
# qet - Main Application Entry Point

import sys
from qet import cli

def main():
    """
    Initializes and runs the qet command-line interface.
    """
    try:
        cli.run()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
