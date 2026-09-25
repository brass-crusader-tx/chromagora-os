#!/usr/bin/env python3
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name('generate_tsunami_sans.py')), run_name='__main__')
