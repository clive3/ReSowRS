#!/usr/bin/env python

###############################################################################
###############################################################################
###############################################################################
##                                                                           ##
##                         START OF IMPORTS                                  ##
##                                                                           ##
##                                                                           ##
import sys
##                                                                           ##
##                                                                           ##
###############################################################################
###############################################################################
##                                                                           ##
##                         START OF FUNCTIONS                                ##
##                                                                           ##
###############################################################################
###############################################################################
##                                                                           ##
##                                                                           ##


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


def printLine(number):
    
    for i in range(number):
        print('*********************************************************************')

##                                                                           ##
##                                                                           ##
###############################################################################
###############################################################################