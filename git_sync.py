import subprocess
import os

os.chdir(r'd:\python_project\creative_master')

subprocess.run(['git', 'add', '-A'], check=True)
subprocess.run(['git', 'commit', '-m', 'Add startup scripts for Windows/macOS/Linux'], check=True)
subprocess.run(['git', 'push', 'origin', 'main'], check=True)

print('Done!')
