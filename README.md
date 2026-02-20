# Projector-desktop

This is a minimalist alternative for the [Projector](https://github.com/bence21/Projector) application that can be downloaded from [songpraise.com](https://www.songpraise.com/#/desktop-app)

The main problem is that the **Projector** app is windows exclusive(and has terrible compatibility with linux wine).

This project could be run in any desktop that supports Python.(maybe there will be builds in the future)

This is mainly in development but already somewhat useable.
You can donwload predetermined bibles in the app or could drop an .SQLite3 bible from [here](https://www.ph4.org/b4_index.php)

Goals:

- [x] Custom dowloadable bible databases
- [ ] Song downloads
- [ ] Create custom songs
- [ ] Screen managment

As this is a project for my needs it will contain only the minimum I need and will not implement everything from the Projector app.

For this is mainly for linux, i found that the pip version of pyside6 does not work well with my linux themes ie. buggy colors.
Solution: download pyside6 using system package manager and create venv using
python -m venv --system-site-packages venv
Fixes color problem.