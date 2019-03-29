"""Crossmap

Usage: python3 crossmap.py command

@author: Tomasz Konopka
"""


import argparse


parser = argparse.ArgumentParser(description="obotools")

# choice of utility
parser.add_argument("command", action="store",
                    help="Name of utility",
                    choices=["build"])


# ############################################################################

if __name__ == "__main__":
    
    config = parser.parse_args()    

