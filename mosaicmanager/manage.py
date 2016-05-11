#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(PARENT)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mosaicmanager.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
