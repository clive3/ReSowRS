#!/usr/bin/env python
import sys


def printProgress(message):

    print(f'progress  >>>  {message}')


def printWarning(message):
        
    print('*******')
    # print (f'warning   \u26A0  {message}')
    print(f'WARNING   @@@  {message}')
    print('*******')
        
        
def printError(message):
        
    print('*******')
    # print (f'ERROR     \u2620  {message}')
    print(f'ERROR     XXX  {message}')
    print('*******')
    sys.exit()
