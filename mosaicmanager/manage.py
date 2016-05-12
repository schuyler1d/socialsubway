#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CURDIR = os.getcwd() 
    sys.path.append(CURDIR) #for local_settings.py
    sys.path.append(PARENT) #for running processes like osaic.py
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mosaicmanager.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
