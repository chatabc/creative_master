import subprocess
import os

os.chdir(r'd:\python_project\creative_master')

commands = [
    ['git', 'add', '.'],
    ['git', 'commit', '-m', 'Initial commit: Creative Master - AI-driven creative inspiration management tool'],
    ['git', 'branch', '-M', 'main'],
    ['git', 'remote', 'add', 'origin', 'https://github.com/chatabc/creative_master.git'],
    ['git', 'push', '-u', 'origin', 'main']
]

for cmd in commands:
    print(f'Running: {" ".join(cmd)}')
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    print('---')

print('Done!')
