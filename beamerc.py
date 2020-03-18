#! /usr/bin/env python3
from PyPDF2 import PdfFileWriter, PdfFileReader
import sys
import os
from tqdm import tqdm
from multiprocessing import Pool

infile = None

try:
    infile = PdfFileReader(sys.argv[1], 'rb')
except IndexError:
    sys.stderr.write(f'Usage: {sys.argv[0]} [ file ]\n')
    sys.exit(-1)
except:
    sys.stderr.write(f'Cannot read input file: {sys.argv[1]}\n')
    sys.exit(-2)

infos = infile.documentInfo.copy()

if len(list(filter(lambda s: 'beamer' in str(s).lower(), infos.values()))) == 0:
    sys.stderr.write('Not a Beamer PDF\n')
    sys.exit(-3)

output = PdfFileWriter()
output_page_nums = []

print('Analyzing...')


def worker(src_page_num: int):
    text = str(infile.getPage(src_page_num).extractText())
    return src_page_num, text.splitlines()[-1]


pool = Pool(15)
results = list(tqdm(pool.imap(worker, range(infile.getNumPages())), total=infile.getNumPages()))
pool.close()
pool.join()

page_nums = {}

for result in results:
    page_nums[result[0]] = result[1]

print('Comparing...')
for i in tqdm(range(1, infile.getNumPages())):
    if page_nums[i] != page_nums[i - 1]:
        output_page_nums.append(i - 1)
output_page_nums.append(-1)

print('Generating...')
for num in tqdm(output_page_nums):
    output.addPage(infile.pages[num])

infos['/Producer'] += ' + BeamerCleaner'
output.addMetadata(infos)

dirname = os.path.dirname(sys.argv[1])
basename = os.path.basename(sys.argv[1]).replace('.pdf', '_C.pdf')
output_name = os.path.join(dirname, basename)

print(f'Writing to {output_name}...')
with open(output_name, 'wb') as f:
    output.write(f)

print('Done.')
