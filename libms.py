import sys
import os

# Add the app directory to the path so imports work correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from ui.gui import main # type: ignore

if __name__ == "__main__":
    main()
