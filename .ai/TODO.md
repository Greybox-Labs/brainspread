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
- [x] when you click a tag it should take you to the tag page which shows all
  blocks and pages with that tag
- [x] when saving a block should parse the text for TODO or similar keywords
  like DONE to create or update the block as the correct type
- [x] should support nested blocks
- [x] hitting backspace on an empty block should delete the block
- [x] clicking a TODOs checkbox should toggle the block to DONE and vice versa
- [x] should style DONE blocks with a strikethrough
- [x] toggleable light/dark mode
- [x] given the previous todo and the user timezone setting, let's add a
  settings page where the user can set their timezone
  and light/dark mode preference
- [ ] should be able to drag and move block ordering and nestings around
- [x] should always use typehints in python code
- [ ] ui/ux for pages
- [x] should test at the api layer and not command. then we dont have to have
  command and form tests, etc.
- [ ] reminders/notifications? kinda useless without push notifications which
  require a mobile app i think?
  - maybe can use something like Pusher? i still think you need APN details for
    that
  - maybe can use Twilio? though Sam did say recently that you have to jump
    through some hoops to get a phone number now
- [x] clicking the "brainspreader" text in the navbar top left should take you
  to the homepage
- [ ] when a user submits a web link, it should be accessed and summarized with
  tags auto-generated from the content
- [ ] when a user submits a web link use semantic search to find similar blocks
  and pages and show them in sidebar
- [ ] blocks should have a context menu popover. right now a cool option would
  be to move to current day
- [ ] clicking dark or light option in settings should toggle the mode
  immediately so the user can see the change

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
- [x] hitting "enter" creates a new block at the bottom, but if you are focused
  on not-the-last block, it should create the next block underneath the current
  block
- [x] hitting "enter" now creates a block under the current block, but only at
  the top level. if you are in a nested block and hit enter, it should create a
  new block as a next immediate sibling of the current nested block
- [ ] hitting "enter" to create a new block when on a note from a previous day,
  it incorrectly creates a new block for the current day instead of under the
  active block
- [ ] when hitting tab on a new block, it indents the block properly, but it
  does not keep focus on the block
- [ ] can't see nested blocks for past daily notes in list view

# Maybe later

- [ ] implement sentence-transformer and chromadb
