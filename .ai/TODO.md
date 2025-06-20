# Features
- [x] daily journal
- [x] refactor into logseq clone
- [x] remove journal entries model since it is no longer being used.
- [x] restyle in a brutalist style with thin lines,
      high contrast colors, and no border radii
- [x] implement python formatting with black. install in Pipfile,
      ensure Pipfile.lock is updated, add a just command, and run it
- [x] implement tests for the commands
- [x] refactor user views to use commands and repositories
- [x] /knowledge page should show historical pages and blocks also
- [x] there should be a sidebar with all tags, pages, and blocks
- [x] when you click a tag it should take you to the tag page which shows all blocks and pages with that tag
- [x] when saving a block should parse the text for TODO or similar keywords like DONE to create or update the block as the correct type
- [x] should support nested blocks
- [ ] hitting backspace on an empty block should delete the block
- [ ] should be able to drag and move block ordering and nestings around
- [ ] should test at the api layer and not command. then we dont have to have command and form tests, etc.
- [ ] ui/ux for pages
- [ ] reminders/notifications?


# Questions
- [ ] Filebase storage vs database? filebase storage could
      be more portable and easier to handle media. hm we'd
      still want some form of metadata for the objects. maybe
      a metadata file with the same name or something? how tenable
      to update if the filename is changed? will the filename be changed?
      how often?

# Bugs
- [x] tags not created when block created, maybe when block is updated too
- [x] is the management command to create a test user necessary?
- [x] the auto save feature on the front end moves selection away from the input
      so it suddenly stops user input and is annoying
- [x] shows login page between page clicks even when logged in

# Usage Notes

## Nested Blocks
Nested blocks are now fully supported! Here's how to use them:

### Creating Nested Blocks
- **Tab**: Press Tab while editing a block to indent it (make it a child of the previous sibling block)
- **Shift+Tab**: Press Shift+Tab while editing a block to outdent it (move it up one level in the hierarchy)
- **Enter**: Create a new block at the same level as the current block
- **Visual Hierarchy**: Child blocks are visually indented with a green left border

### Features
- **Unlimited Nesting**: You can create as many levels of nesting as needed
- **Drag and Drop**: Use Tab/Shift+Tab to reorganize block hierarchy
- **Circular Reference Protection**: The system prevents creating circular references
- **Order Preservation**: Block order is maintained within each parent context
- **Auto-save**: Changes to block hierarchy are automatically saved

### Keyboard Shortcuts
- `Tab` - Indent current block (make it a child of previous sibling)
- `Shift+Tab` - Outdent current block (move up one level)
- `Enter` - Create new block at same level
- `Arrow Up/Down` - Navigate between blocks while editing

### Backend Support
- Full API support for parent/child relationships
- Comprehensive test coverage for nested functionality
- Command pattern implementation for all block operations
- Proper validation and error handling
