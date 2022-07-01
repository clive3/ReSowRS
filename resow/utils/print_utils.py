#!/usr/bin/env python
import sys


def _printProgress(message):

    print(f'progress  >>>  {message}')


def _printWarning(message):
        
    print('*******')
    # print (f'warning   \u26A0  {message}')
    print(f'WARNING   @@@  {message}')
    print('*******')
        
        
def _printError(message):
        
    print('*******')
    # print (f'ERROR     \u2620  {message}')
    print(f'ERROR     XXX  {message}')
    print('*******')
    sys.exit()
