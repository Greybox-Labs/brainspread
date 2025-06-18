# Features
- [x] daily journal
- [x] refactor into logseq clone
- [x] remove journal entries model since it is no longer being used.
- [ ] restyle in a brutalist style with thin lines,
      high contrast colors, and no border radii
- [x] implement python formatting with black. install in Pipfile,
      ensure Pipfile.lock is updated, add a just command, and run it
- [x] implement tests for the commands
- [ ] refactor user views to use commands and repositories

# Questions
- [ ] Filebase storage vs database? filebase storage could
      be more portable and easier to handle media. hm we'd
      still want some form of metadata for the objects. maybe
      a metadata file with the same name or something? how tenable
      to update if the filename is changed? will the filename be changed?
      how often?

# Bugs
- [x] tags not created when block created, maybe when block is updated too
- [ ] is the management command to create a test user necessary?
