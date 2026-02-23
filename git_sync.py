import subprocess
import os

os.chdir(r'd:\python_project\creative_master')

subprocess.run(['git', 'add', '-A'], check=True)
subprocess.run(['git', 'commit', '-m', 'Add README and clear test data'], check=True)
subprocess.run(['git', 'push', 'origin', 'main'], check=True)

print('Done!')
