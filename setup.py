from pymodaq.resources.setup_plugin import setup
from pathlib import Path

print(f"Running setup in: {Path(__file__).parent}")
setup(Path(__file__).parent)
