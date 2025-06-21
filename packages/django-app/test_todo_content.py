#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append('/code/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from knowledge.models import Block
from knowledge.commands import ToggleBlockTodoCommand

# Find a block with "google tasks" in content
blocks = Block.objects.filter(content__icontains="google tasks")
print(f"Found {blocks.count()} blocks with 'google tasks'")

for block in blocks:
    print(f"Block ID: {block.uuid}")
    print(f"Content: '{block.content}'")
    print(f"Block type: {block.block_type}")
    print("---")

# Test the regex replacement manually
from knowledge.commands.toggle_block_todo_command import ToggleBlockTodoCommand

cmd = ToggleBlockTodoCommand(None, None)
test_content = "TODO google tasks"
result = cmd._replace_todo_with_done(test_content)
print(f"Test: '{test_content}' -> '{result}'")

test_content2 = "DONE google tasks"  
result2 = cmd._replace_done_with_todo(test_content2)
print(f"Test: '{test_content2}' -> '{result2}'")