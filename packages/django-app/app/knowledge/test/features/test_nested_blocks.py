from django.test import TestCase
from django.core.exceptions import ValidationError

from knowledge.commands.create_block_command import CreateBlockCommand
from knowledge.commands.update_block_command import UpdateBlockCommand
from knowledge.test.helpers import UserFactory, PageFactory


class TestNestedBlocksIntegration(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.page = PageFactory(user=cls.user)

    def test_should_create_and_manage_nested_hierarchy(self):
        """Test creating and managing a complete nested block hierarchy"""
        # Create root blocks
        root1_cmd = CreateBlockCommand(
            user=self.user, page=self.page, content="Root block 1", parent=None, order=0
        )
        root1 = root1_cmd.execute()

        root2_cmd = CreateBlockCommand(
            user=self.user, page=self.page, content="Root block 2", parent=None, order=1
        )
        root2 = root2_cmd.execute()

        # Verify root blocks
        self.assertEqual(root1.get_depth(), 0)
        self.assertEqual(root2.get_depth(), 0)
        self.assertIsNone(root1.parent)
        self.assertIsNone(root2.parent)

        # Create child blocks
        child1_cmd = CreateBlockCommand(
            user=self.user,
            page=self.page,
            content="Child of root 1",
            parent=root1,
            order=0,
        )
        child1 = child1_cmd.execute()

        child2_cmd = CreateBlockCommand(
            user=self.user,
            page=self.page,
            content="Another child of root 1",
            parent=root1,
            order=1,
        )
        child2 = child2_cmd.execute()

        # Verify child blocks
        self.assertEqual(child1.get_depth(), 1)
        self.assertEqual(child2.get_depth(), 1)
        self.assertEqual(child1.parent, root1)
        self.assertEqual(child2.parent, root1)

        # Create grandchild
        grandchild_cmd = CreateBlockCommand(
            user=self.user,
            page=self.page,
            content="Grandchild block",
            parent=child1,
            order=0,
        )
        grandchild = grandchild_cmd.execute()

        # Verify grandchild
        self.assertEqual(grandchild.get_depth(), 2)
        self.assertEqual(grandchild.parent, child1)

        # Test indentation (moving child2 under child1)
        update_cmd = UpdateBlockCommand(
            user=self.user, block_id=child2.uuid, parent_id=child1.uuid, order=1
        )
        update_cmd.execute()
        child2.refresh_from_db()

        # Verify indentation
        self.assertEqual(child2.get_depth(), 2)
        self.assertEqual(child2.parent, child1)

        # Test outdentation (moving grandchild to root)
        update_cmd = UpdateBlockCommand(
            user=self.user, block_id=grandchild.uuid, parent_id=None, order=2
        )
        update_cmd.execute()
        grandchild.refresh_from_db()

        # Verify outdentation
        self.assertEqual(grandchild.get_depth(), 0)
        self.assertIsNone(grandchild.parent)

    def test_should_maintain_hierarchy_relationships(self):
        """Test that hierarchy relationships are properly maintained"""
        # Create hierarchy: root -> child -> grandchild
        root_cmd = CreateBlockCommand(
            user=self.user, page=self.page, content="Root block", parent=None, order=0
        )
        root = root_cmd.execute()

        child_cmd = CreateBlockCommand(
            user=self.user, page=self.page, content="Child block", parent=root, order=0
        )
        child = child_cmd.execute()

        grandchild_cmd = CreateBlockCommand(
            user=self.user,
            page=self.page,
            content="Grandchild block",
            parent=child,
            order=0,
        )
        grandchild = grandchild_cmd.execute()

        # Test get_children
        root_children = root.get_children()
        self.assertEqual(len(root_children), 1)
        self.assertEqual(root_children[0], child)

        child_children = child.get_children()
        self.assertEqual(len(child_children), 1)
        self.assertEqual(child_children[0], grandchild)

        # Test get_descendants
        root_descendants = root.get_descendants()
        self.assertEqual(len(root_descendants), 2)
        self.assertIn(child, root_descendants)
        self.assertIn(grandchild, root_descendants)

    def test_should_preserve_block_order_within_parent(self):
        """Test that block order is preserved within parent context"""
        # Create parent
        parent_cmd = CreateBlockCommand(
            user=self.user, page=self.page, content="Parent block", parent=None, order=0
        )
        parent = parent_cmd.execute()

        # Create children with specific orders
        child1_cmd = CreateBlockCommand(
            user=self.user, page=self.page, content="Child 1", parent=parent, order=0
        )
        child1 = child1_cmd.execute()

        child2_cmd = CreateBlockCommand(
            user=self.user, page=self.page, content="Child 2", parent=parent, order=1
        )
        child2 = child2_cmd.execute()

        child3_cmd = CreateBlockCommand(
            user=self.user, page=self.page, content="Child 3", parent=parent, order=2
        )
        child3 = child3_cmd.execute()

        # Verify order
        children = parent.get_children()
        self.assertEqual(len(children), 3)
        self.assertEqual(children[0], child1)
        self.assertEqual(children[1], child2)
        self.assertEqual(children[2], child3)

    def test_should_handle_data_integrity_validation(self):
        """Test that data integrity is maintained across operations"""
        # Create a block hierarchy
        root_cmd = CreateBlockCommand(
            user=self.user, page=self.page, content="Root block", parent=None, order=0
        )
        root = root_cmd.execute()

        child_cmd = CreateBlockCommand(
            user=self.user, page=self.page, content="Child block", parent=root, order=0
        )
        child = child_cmd.execute()

        # Verify parent-child relationship integrity
        self.assertEqual(child.parent, root)
        self.assertEqual(child.parent.user, self.user)
        self.assertEqual(child.user, self.user)
        self.assertEqual(root.user, self.user)

        # Verify page relationships
        self.assertEqual(child.page, self.page)
        self.assertEqual(root.page, self.page)
        self.assertEqual(self.page.user, self.user)
