#!/usr/bin/python3
from pathlib import Path
import base64
import shutil
import sys
import os

FIFT_LIBS_LIST = [lib + '.fif' for lib in 'Fift Asm AsmTests TonUtil Lists Color'.split(' ')]
CONTRACTS_LIST = 'nft collection'.split(' ')

base_path = Path(__file__).parent
fift_path = Path(os.environ['FIFTPATH']) / 'toncli/lib/fift-libs'

print('====== Starting build ====================')

os.system('cls')    # clears screen + enables escape sequences

for fift_lib in FIFT_LIBS_LIST:
    shutil.copy(fift_path / fift_lib, base_path / fift_lib)

print('====== Loaded libs for toncli ============')

# with open(ap(base_path + '/fift/exotic.fif')) as f:
#   exotic_patch = f.read()
# 
# with open(ap(base_path + '/Asm.fif'), 'a') as f: f.write(exotic_patch)
# with open(ap(base_path + '/AsmTests.fif'), 'a') as f: f.write(exotic_patch)
# 
# print('====== Patched Fift libraries ============')
# 
# os.chdir(base_path)
# os.system('toncli run_tests >toncli.log 2>toncli.err')
# os.system('python show-log.py')
# 
# print('====== Ran tests =========================')

os.system('toncli build')

print('====== Built contract in prod mode =======')

for contract in CONTRACTS_LIST:
    with (base_path / f'build/{contract}.fif').open('a') as f:
        f.write(f'\nboc>B "assets/{contract}-code.boc" B>file')
    
    os.system(f'toncli fift run build/{contract}.fif')
    print(f'====== Saved {repr(contract)} in BOC representation')

if '--noclean' not in sys.argv:
    for fift_lib in FIFT_LIBS_LIST: os.remove(base_path / fift_lib)
    print('====== Deleted Fift libs =================')
