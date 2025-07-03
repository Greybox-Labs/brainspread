# Features

## ai features
- [x] should be able to copy content from code blocks in ai chat view
- [x] ai chat messages should have a context menu popover with option to copy
  content
- [ ] when a user submits a web link, it should be accessed and summarized with
  tags auto-generated from the content
- [ ] when a user submits a web link use semantic search to find similar blocks
  and pages and show them in sidebar

## general usage
- [x] ui/ux for pages
  - [x] create new page
  - [x] history sidebar already has pages sorted by most recently modified
  - [x] only one path for page (instead of page vs daily note, bc they're all 
    pages)
  - 
- [ ] cmd + space like mac spotlight to search for pages and blocks
- [ ] reminders/notifications? kinda useless without push notifications which
  require a mobile app i think?
  - maybe can use something like Pusher? i still think you need APN details for
    that
  - maybe can use Twilio? though Sam did say recently that you have to jump
    through some hoops to get a phone number now
- [ ] blocks should have a context menu popover. right now a cool option would
  be to move to current day
- [ ] should be able to drag and move block ordering and nestings around
- [ ] clicking dark or light option in settings should toggle the mode
  immediately so the user can see the change
- [ ] should be able to click on a historical daily note to go to that daily note's
  page

## mobile usage
- [x] better use of space on mobile
  - [x] daily note view 
  - [x] ai chat 
- [ ] ability to reorder blocks. drag n drop would be great, but maybe just an 
  "editing view" w/ up/down arrow would be sufficient for now

# Optimizations
- [ ] need to cleanup frontend routes, django templates, and the vue app
- [ ] infinite scroll for ai chat history
- [ ] infinite scroll for daily notes

# Cleanup
- [x] remove empty __init__.py files that are not needed
- [x] python imports should not be done inside methods, they should be imported
  at the top of the file
- [x] backend forms that have a field that describes a related model should use
  the `ModelChoiceField` instead of `CharField`. you can still pass the pk when
  creating the form and it will find the correct model instance, you don't have
  to pass the entire model instance. the arg to ModelChoiceField should be
  something like `queryset=SomeRepository.get_queryset()`. A good example is
  UpdateBlockForm.
  ```python
  class UpdateBlockForm(BaseForm):
    user = forms.ModelChoiceField(queryset=UserRepository.get_queryset())
    block_id = forms.CharField(required=True)
  ```
  The `user` field is defined correctly, but the `block_id` field needs to be
  changed to
  `block = forms.ModelChoiceField(queryset=BlockRepository.get_queryset())`. We
  need to fix this issue for all forms in our app
- [x] core commands's constructors should only take forms, not other args
- [ ] fix ai_chat forms to take UUIDModelChoiceField, then fix frontend
- [ ] not all view functions follow conventions. there is a fair amount of
  business logic in ai_chat view files
- [x] knowledge views dont use response types

# Questions

- [ ] Filebase storage vs database? filebase storage could
  be more portable and easier to handle media. hm we'd
  still want some form of metadata for the objects. maybe
  a metadata file with the same name or something? how tenable
  to update if the filename is changed? will the filename be changed?
  how often?

# Bugs

- [x] currently we can only move undone blocks to current day, but the option is there when
  viewing any daily note. create a MoveUndoneTodosForm that has a `user` field
  and an optional field named `target_date`, with no default value. Next, you 
  need to refactor MoveUndoneTodosCommand to use this form, and then update the
  command logic to handle the `target_date` field. If the field is not provided,
  it should default to the current date. If it is provided, it should move the
  undone blocks to that date instead of the current date.
- [ ] hitting "enter" to create a new block when on a note from a previous day,
  it incorrectly creates a new block for the current day instead of under the
  active block
- [ ] when hitting tab on a new block, it indents the block properly, but it
  does not keep focus on the block
- [ ] can't see nested blocks for past daily notes in list view
  - maybe this isn't the worst ui, but we should show that there are nested
    blocks and either let the user expand them there or let the user click into
    the note. the latter should be possible regardless.

# Maybe later

- [ ] implement sentence-transformer and chromadb
- [ ] refactor the data models
  - instead of having a Page, Block, Tag, could we just have Page and Block, and
  to support "tags", we would allow a Block to belong to many Pages. a "tag"
  would mean a block belongs to that Page and the frontend would render and
  parse the information as "tags" visually.