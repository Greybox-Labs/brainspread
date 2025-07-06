#!/usr/bin/env python
import os
import sys
import django

# Add the app directory to Python path
sys.path.append('/Users/jessesnyder/code/projects/brainspread-brain-dump-app/astria-brainspread-mvp/brainspread/packages/django-app')
os.chdir('/Users/jessesnyder/code/projects/brainspread-brain-dump-app/astria-brainspread-mvp/brainspread/packages/django-app')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from knowledge.models import Block

# Check blocks containing hamburger hashtag
blocks = Block.objects.filter(content__icontains='#hamburger')
print(f"Found {blocks.count()} blocks containing '#hamburger':")
for block in blocks:
    print(f"Block {block.uuid}: '{block.content}'")

# Check blocks containing pizza-time hashtag  
blocks2 = Block.objects.filter(content__icontains='#pizza-time')
print(f"\nFound {blocks2.count()} blocks containing '#pizza-time':")
for block in blocks2:
    print(f"Block {block.uuid}: '{block.content}'")