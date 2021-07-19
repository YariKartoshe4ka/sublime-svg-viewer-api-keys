"""
Dependencies:
colorama==0.4.4
requests==2.24.0
tabulate==0.8.9
"""

from argparse import ArgumentParser
from math import ceil
from re import match

import cloudconvert
import colorama
from tabulate import tabulate


colorama.init()

parser = ArgumentParser()
parser.add_argument(dest='file', help='Path to file with keys')
parser.add_argument('-s', '--structure', dest='structure', action='store_true', help='Test structure of token to match JWT token')
parser.add_argument('-c', '--credits', dest='credits', action='store_true', help='Print available credits')
parser.add_argument('-j', '--job', dest='job', action='store_true', help='Test token by creating job (SVG to PNG)')
parser.add_argument('-f', '--force', dest='force', action='store_true', help='Continue testing current token if previous test was failed')

args = parser.parse_args()

all_keys = 0
with open(args.file) as file:
    for key in file:
        all_keys += 1

percent_per_key = 100 / all_keys

headers = ['Key']

if args.structure:
    headers.append('Structure')

if args.credits:
    headers.append('Credits')

if args.job:
    headers.append('Job')

data = []

with open(args.file) as file:
    line = 0

    for key in file:
        line += 1
        data.append([line])

        API_KEY = key.lstrip().rstrip()
        cloudconvert.configure(api_key=API_KEY)

        if args.structure:
            pattern = r'(.+)\.(.+)\.(.*)'
            data[-1].append(bool(match(pattern, API_KEY)))

        if args.credits:
            if len(data[-1]) and not data[-1][-1] and not args.force:
                data[-1].append(None)
            else:
                try:
                    user = cloudconvert.User.user()
                except:  # noqa: E722
                    data[-1].append(False)
                else:
                    data[-1].append(user['credits'])

        if args.job:
            if len(data[-1]) and not data[-1][-1] and not args.force:
                data[-1].append(None)
            else:
                try:
                    job = cloudconvert.Job.create(payload={
                        'tasks': {
                            'import-svg': {
                                'operation': 'import/upload'
                            },
                            'convert-svg-to-png': {
                                'operation': 'convert',
                                'input_format': 'svg',
                                'output_format': 'png',
                                'engine': 'inkscape',
                                'input': [
                                    'import-svg'
                                ],
                                'pixel_density': 96
                            },
                            'export-png': {
                                'operation': 'export/url',
                                'input': [
                                    'convert-svg-to-png'
                                ],
                                'inline': False,
                                'archive_multiple_files': False
                            }
                        }
                    })

                    for task in job['tasks']:
                        if task['operation'] == 'import/upload':
                            upload_task_id = task['id']
                        elif task['operation'] == 'export/url':
                            export_task_id = task['id']

                    upload_task = cloudconvert.Task.find(id=upload_task_id)
                    export_task = cloudconvert.Task.find(id=export_task_id)

                    cloudconvert.Job.delete(job['id'])
                except:  # noqa: E722
                    data[-1].append(False)
                else:
                    data[-1].append(True)

        print(f'{min(ceil(percent_per_key * line * 100) / 100, 100)}%', end='\r', flush=True)


for i in range(len(data)):
    for j in range(len(data[i])):
        if data[i][j] is True:
            data[i][j] = f'{colorama.Back.GREEN}Passed{colorama.Style.RESET_ALL}'
        elif data[i][j] is False:
            data[i][j] = f'{colorama.Back.RED}Failed{colorama.Style.RESET_ALL}'
        elif data[i][j] is None:
            data[i][j] = f'{colorama.Back.LIGHTBLACK_EX}Skipped{colorama.Style.RESET_ALL}'


print()
print(tabulate(data, headers=headers, tablefmt='github'))
