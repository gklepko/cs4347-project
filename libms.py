import sys
import os

# Add the app directory to the path so imports work correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.ui.gui import main

if __name__ == "__main__":
    main()
