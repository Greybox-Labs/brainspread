#!/usr/bin/env python3
"""
Manual test script for nested blocks functionality.
This script creates blocks and tests the indentation/outdentation logic.
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
sys.path.append('/code/app')
django.setup()

from core.models import User
from knowledge.models import Page, Block
from knowledge.commands.create_block_command import CreateBlockCommand
from knowledge.commands.update_block_command import UpdateBlockCommand

def test_nested_blocks():
    print("🧪 Testing Nested Blocks Functionality")
    print("=" * 50)
    
    # Get or create test user
    user = User.objects.first()
    if not user:
        print("❌ No user found! Please create a user first.")
        return
    
    print(f"👤 Using user: {user.email}")
    
    # Get or create test page
    page = Page.objects.filter(user=user).first()
    if not page:
        from knowledge.commands.create_page_command import CreatePageCommand
        create_page_cmd = CreatePageCommand(
            user=user,
            title="Test Page",
            content="Test page for nested blocks",
            page_type="regular"
        )
        page = create_page_cmd.execute()
    
    print(f"📄 Using page: {page.title} ({page.uuid})")
    print()
    
    # Clean up any existing test blocks
    Block.objects.filter(user=user, page=page, content__startswith="TEST:").delete()
    
    # Test 1: Create root blocks
    print("1️⃣  Creating root blocks...")
    root1_cmd = CreateBlockCommand(
        user=user,
        page=page,
        content="TEST: Root block 1",
        parent=None,
        order=0
    )
    root1 = root1_cmd.execute()
    print(f"   ✅ Created root block: {root1.content}")
    
    root2_cmd = CreateBlockCommand(
        user=user,
        page=page,
        content="TEST: Root block 2",
        parent=None,
        order=1
    )
    root2 = root2_cmd.execute()
    print(f"   ✅ Created root block: {root2.content}")
    print()
    
    # Test 2: Create child blocks
    print("2️⃣  Creating child blocks...")
    child1_cmd = CreateBlockCommand(
        user=user,
        page=page,
        content="TEST: Child of root 1",
        parent=root1,
        order=0
    )
    child1 = child1_cmd.execute()
    print(f"   ✅ Created child block: {child1.content} (depth: {child1.get_depth()})")
    
    child2_cmd = CreateBlockCommand(
        user=user,
        page=page,
        content="TEST: Another child of root 1",
        parent=root1,
        order=1
    )
    child2 = child2_cmd.execute()
    print(f"   ✅ Created child block: {child2.content} (depth: {child2.get_depth()})")
    print()
    
    # Test 3: Create grandchild blocks
    print("3️⃣  Creating grandchild blocks...")
    grandchild_cmd = CreateBlockCommand(
        user=user,
        page=page,
        content="TEST: Grandchild block",
        parent=child1,
        order=0
    )
    grandchild = grandchild_cmd.execute()
    print(f"   ✅ Created grandchild block: {grandchild.content} (depth: {grandchild.get_depth()})")
    print()
    
    # Test 4: Test parent update (simulating Tab indentation)
    print("4️⃣  Testing indentation (moving child2 under child1)...")
    update_cmd = UpdateBlockCommand(
        user=user,
        block_id=child2.uuid,
        parent_id=child1.uuid,
        order=1
    )
    updated_child2 = update_cmd.execute()
    child2.refresh_from_db()
    print(f"   ✅ Moved block: {child2.content} (new depth: {child2.get_depth()})")
    print()
    
    # Test 5: Test outdentation (moving block to root)
    print("5️⃣  Testing outdentation (moving grandchild to root level)...")
    update_cmd = UpdateBlockCommand(
        user=user,
        block_id=grandchild.uuid,
        parent_id=None,
        order=2
    )
    updated_grandchild = update_cmd.execute()
    grandchild.refresh_from_db()
    print(f"   ✅ Moved block to root: {grandchild.content} (new depth: {grandchild.get_depth()})")
    print()
    
    # Test 6: Display hierarchy
    print("6️⃣  Final hierarchy:")
    root_blocks = page.get_root_blocks().filter(content__startswith="TEST:")
    
    def print_block_tree(block, indent=0):
        prefix = "   " * indent + ("└─ " if indent > 0 else "")
        print(f"   {prefix}{block.content} (order: {block.order}, depth: {block.get_depth()})")
        for child in block.get_children().order_by('order'):
            print_block_tree(child, indent + 1)
    
    for root_block in root_blocks.order_by('order'):
        print_block_tree(root_block)
    print()
    
    # Test 7: Test circular reference protection
    print("7️⃣  Testing circular reference protection...")
    try:
        # Try to make root1 a child of its own child
        circular_cmd = UpdateBlockCommand(
            user=user,
            block_id=root1.uuid,
            parent_id=child1.uuid
        )
        circular_cmd.execute()
        print("   ❌ Circular reference was NOT prevented!")
    except Exception as e:
        print(f"   ✅ Circular reference prevented: {str(e)}")
    print()
    
    # Test 8: Verify data integrity
    print("8️⃣  Verifying data integrity...")
    all_test_blocks = Block.objects.filter(user=user, content__startswith="TEST:")
    total_blocks = all_test_blocks.count()
    print(f"   📊 Total test blocks: {total_blocks}")
    
    for block in all_test_blocks:
        if block.parent:
            # Verify parent relationship is valid
            if block.parent.user != user:
                print(f"   ❌ Invalid parent relationship for {block.content}")
            else:
                print(f"   ✅ Valid parent relationship: {block.content} -> {block.parent.content}")
        else:
            print(f"   ✅ Root block: {block.content}")
    
    print()
    print("🎉 Nested blocks test completed!")
    print("=" * 50)

if __name__ == "__main__":
    test_nested_blocks()