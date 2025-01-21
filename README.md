# LocalBooru
Lightweight, fully local booru style app
![123](https://github.com/user-attachments/assets/0e0dfff0-c16f-40f6-9996-4d049e682d44)
![223](https://github.com/user-attachments/assets/777ceab8-f2b5-4145-9731-6983738efc79)
![333](https://github.com/user-attachments/assets/78db6039-0d89-47f4-876f-8912e14a209b)
## Description

As Wikitionary says:

* [booru](https://en.wiktionary.org/wiki/booru) (**plural** boorus)
    1. (**Internet**) A form of imageboard where images are categorized with tags. 

As many booru sites are imageboards hosted online, there was a need for more private one - hosted localy.

This project is written in Python with use of Flask and Sqlalchemy.
I created it as a tool to make my GameDev insirational workflow easier, by allowing me to search files by tags.

### Main Features
1. Fully local
2. Add/ remove tags from media
3. Tag categories (e.g. site, author etc.) with custom colors
4. List of most common tags
5. Searchbar with autofill
6. Search with multiple tags
7. Random media to show
8. Next/ Previous media buttons
9. Media scale change (not fully functional)

## Getting Started

### Run the app
1. install the requirements
2. run the app.py file
3. database booru.db will be created in the project directory
4. the app will launch at http://127.0.0.1:5000/

### Add files to database
1. click "Scan and Tag" button
2. paste local directory with your files
3. (optional) add tags to all scanned files
4. Click "Scan directory"
5. (optional if tags were added)Tags will be added or created and added if they does not exist yet.

### Manage tags
Tags can be managed in the "Manage Tags" section.
You can:
- add/ change a category for a tag -> e.g. for tag "pinterest", category "website" can be added
- remove category from tag
- delete tag (will be deleted from the database entries)

### Add/ remove tags from media
After you click "Tag" below a media thumbnail, you will be able to add multiple tag (comma separated) and remove multiple tag (comma separated)

### Customize

You can customize the tag categories and their colors.

* Customize tag categories and their shown order in app.py

```
category_order = {
    'source': 0, #pinterest, instagram etc.
    'type': 1, #concept_art, screenshot etc.
    'author': 2, #author of the work
    'ip': 3, #what game, movie etc. its from
    'meta': 4, #video, photo etc.
    'element': 5 #UI, HUD, Options Menu etc.
}
```

* Customize category colors in static/style.css

```
.tag-source {
    background-color: #947927;
}

.tag-type {
    background-color: #7f00ae;
}

.tag-author {
    background-color: #2E9028;
}

.tag-meta {
    background-color: #b26500;
}

.tag-default {
    background-color: #770000;
}

.tag-element {
    background-color: #c4b702;
}

.tag-ip {
    background-color: #3904b6;
}
```

### Working with video files
As video files tend to be heavy, they are not displayed in the main grid of the app.
Insted, they are shown as images with green border and can be played only when in selected for tagging.
It is not ideal, but I have created additional tool named thumb_create.py that can allow you to create thumbnails fast.
When you run it, you have to provide the source directory of your video files and then create thumbnails from given timestamp.
You have to name the file the same as the number, the media you try to add is refering too. 
E.g. You need thumbnail for media nr. 4, you save the file with the app as 4.jpg

## Dependencies

* Python==3.10
* blinker==1.9.0
* click==8.1.8
* colorama==0.4.6
* ffmpeg==1.4
* Flask==3.1.0
* itsdangerous==2.2.0
* Jinja2==3.1.5
* MarkupSafe==3.0.2
* SQLAlchemy==2.0.36
* typing_extensions==4.12.2
* Werkzeug==3.1.3

## Version History

* 0.1
    * Initial Release
