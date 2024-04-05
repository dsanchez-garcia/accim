import subprocess
from pathlib import Path

idfs = list(Path('.').resolve().glob('*.idf'))

TRANSITION_CLI_DIR = Path('C:\EnergyPlusV23-2-0\PreProcess\IDFVersionUpdater')

transition_exe = TRANSITION_CLI_DIR / 'Transition-V9-4-0-to-V23-2-0'

subprocess.check_output([transition_exe, idfs[0]], cwd=TRANSITION_CLI_DIR)