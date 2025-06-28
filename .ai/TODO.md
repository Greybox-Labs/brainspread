# Features

- [ ] should be able to drag and move block ordering and nestings around
- [ ] ui/ux for pages
- [ ] reminders/notifications? kinda useless without push notifications which
  require a mobile app i think?
  - maybe can use something like Pusher? i still think you need APN details for
    that
  - maybe can use Twilio? though Sam did say recently that you have to jump
    through some hoops to get a phone number now
- [ ] when a user submits a web link, it should be accessed and summarized with
  tags auto-generated from the content
- [ ] when a user submits a web link use semantic search to find similar blocks
  and pages and show them in sidebar
- [ ] blocks should have a context menu popover. right now a cool option would
  be to move to current day
- [ ] clicking dark or light option in settings should toggle the mode
  immediately so the user can see the change
- [ ] should be able to click on a historical daily note to go to that daily note's
  page

# Optimizations

- [ ] infinite scroll for ai chat history + 
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
  business logic in view files

# Questions

- [ ] Filebase storage vs database? filebase storage could
  be more portable and easier to handle media. hm we'd
  still want some form of metadata for the objects. maybe
  a metadata file with the same name or something? how tenable
  to update if the filename is changed? will the filename be changed?
  how often?

# Bugs

- [ ] hitting "enter" to create a new block when on a note from a previous day,
  it incorrectly creates a new block for the current day instead of under the
  active block
- [ ] when hitting tab on a new block, it indents the block properly, but it
  does not keep focus on the block
- [ ] can't see nested blocks for past daily notes in list view

# Maybe later

- [ ] implement sentence-transformer and chromadb