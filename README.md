# Kobo-Composite-Markup-Generator
I am extremely annoyed with Kobo for not providing a valid solution for exporting markups (I own the Kobo Libre Color 2). So I am writing my own.

I currently have a working python script that relies on the `pillow` and `cairosvg` python libraries. The file must be placed in the `.kobo/markups` directory, where it will iterate through all files, 'remember' any files that are svg and jpg, and use `cairosvg` to 1.) convert `svg`'s to `png`'s and 2.) overlay the newly created `png`'s with the  original `jpg` pages. 

This script works based on two assumptions:
1. that it is located in the `.kobo/markups` directory,
2. and that each 'markup' consists of a `jpg` file of the page that was written on and an indentically named `svg` file.
3. a python virtual environement is being used, with `cairosvg` and `pillow` python libraries already installed.

As of Dec. 21, 2024, I consider this project incomplete. I wrote this script in 2ish hours and would like to have a standalone executeable with a simple GUI that will be accessible to non-technical people. I use Calibre as well, so if I could figure out how to make this a plugin that would be even better.

---

_This readme is a work and progress, detailed instructions will follow._

---

**I am not responsible for any unintended consequences that may arise from using this script. By using this script, you acknowledge that you are solely responsible for reviewing it, understanding its behavior, and accepting all resulting outcomes.**
