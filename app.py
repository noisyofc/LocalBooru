# app.py
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, flash, jsonify
from flask import session as flask_session
import os
import ffmpeg
from models import Session, Image, Tag, init_db
import math  # For calculating total pages
from sqlalchemy import func
import random

app = Flask(__name__)
app.secret_key = 'some_secret_key'  # For flash messages

CURRENT_DB = 'sqlite:///booru.db'  # Default database path
session = None  # Placeholder for the database session

def get_db_directory():
    # Ensure CURRENT_DB points to the full database file path
    db_name = os.path.basename(CURRENT_DB).replace('.db', '')  # Remove '.db'
    return db_name

def set_database(db_path):
    global session, CURRENT_DB
    CURRENT_DB = db_path
    print(f"DEBUG: Switching database to {CURRENT_DB}")  # Debugging statement
    Session = init_db(db_path)
    session = Session()

    # Ensure the directory exists for thumbnails
    db_directory = get_db_directory()
    thumbnails_path = os.path.join('static', 'thumbnails', db_directory)
    if not os.path.exists(thumbnails_path):
        print(f"DEBUG: Creating thumbnail directory at {thumbnails_path}")
        os.makedirs(thumbnails_path)
set_database(CURRENT_DB)
session = Session()

# Supported file extensions for images and videos
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif')
VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv')

# Number of items to display per page
ITEMS_PER_PAGE = 48

import random

@app.route('/switch_db', methods=['POST'])
def switch_db_inline():
    new_db = request.form.get('db_path')
    if new_db:
        if not os.path.exists(new_db):
            flash('Database file does not exist.', 'error')
        else:
            set_database(f'sqlite:///{new_db}')
            flash(f'Successfully switched to database: {new_db}', 'success')
    return redirect(request.referrer or url_for('index'))  # Redirect back to the same page

@app.context_processor
def inject_db_info():
    db_files = [f for f in os.listdir('.') if f.endswith('.db')]
    db_directory = get_db_directory()
    print(f"DEBUG: Current database directory: {db_directory}")  # Debugging statement
    return {
        'db_files': db_files,
        'current_db': CURRENT_DB,
        'db_directory': db_directory,
    }





@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    total_items = session.query(Image).count()
    total_pages = math.ceil(total_items / ITEMS_PER_PAGE)
    images = session.query(Image).order_by(Image.id.desc()).limit(ITEMS_PER_PAGE).offset((page - 1) * ITEMS_PER_PAGE).all()

    # Fetch the most common tags
    common_tags = session.query(
        Tag.name,
        Tag.category,
        func.count(Tag.id).label('count')
    ).join(Image.tags).group_by(Tag.name, Tag.category).order_by(func.count(Tag.id).desc()).all()

    return render_template('index.html', images=images, page=page, total_pages=total_pages, common_tags=common_tags)


@app.route('/random')
def random_media():
    # Get all media IDs from the database
    media_ids = session.query(Image.id).all()
    
    # Check if there are any media files in the database
    if not media_ids:
        flash("No media available.")
        return redirect(url_for('index'))

    # Select a random ID
    random_id = random.choice([media.id for media in media_ids])

    # Redirect to the tag page for the random media
    return redirect(url_for('tag_media', image_id=random_id))

@app.route('/tags', methods=['GET', 'POST'])
def manage_tags():
    if request.method == 'POST':
        # Handle tag deletion
        tag_id = request.form.get('tag_id')
        tag = session.query(Tag).filter_by(id=tag_id).first()
        if tag:
            session.delete(tag)
            session.commit()
            flash(f'Tag "{tag.name}" deleted successfully!', 'success')
        else:
            flash('Tag not found!', 'error')

    # Fetch all tags to display, ordered by newest first (Tag.id desc)
    tags = session.query(Tag).order_by(Tag.id.desc()).all()
    
    return render_template('tags.html', tags=tags)

# New route to scan a custom directory
@app.route('/scan', methods=['GET', 'POST'])
def scan_media():
    if request.method == 'POST':
        directory = request.form.get('directory')
        tags_input = request.form.get('tags', '').split(',')
        tags = [tag_name.strip() for tag_name in tags_input if tag_name.strip()]
        
        if directory and os.path.exists(directory):
            # Recursively scan the directory for images and videos
            for root, dirs, files in os.walk(directory):
                for filename in files:
                    file_path = os.path.join(root, filename)

                    # Check if the file is an image or a video
                    if filename.lower().endswith(IMAGE_EXTENSIONS + VIDEO_EXTENSIONS):
                        # Check if the file is already in the database
                        media_file = session.query(Image).filter_by(path=file_path).first()

                        if not media_file:
                            # If the file is new, add it to the database
                            media_file = Image(path=file_path)
                            session.add(media_file)
                            session.commit()

                        # Now, we process the tags for the media (whether new or existing)
                        for tag_name in tags:
                            if tag_name:
                                tag = session.query(Tag).filter_by(name=tag_name).first()
                                if not tag:
                                    # If the tag doesn't exist, create a new tag
                                    tag = Tag(name=tag_name)
                                if tag not in media_file.tags:
                                    # Add the tag to the media if it's not already associated
                                    media_file.tags.append(tag)
                        session.commit()

        flash('Media files scanned and tags applied successfully!')
        return redirect(url_for('index'))

    return render_template('scan.html')

@app.route('/tag_suggestions', methods=['GET'])
def tag_suggestions():
    query = request.args.get('q', '')
    if query:
        # Split the input by commas and strip whitespace
        tags = [tag.strip() for tag in query.split(',') if tag.strip()]
        
        # Get the last tag (the one being typed) to suggest from
        last_tag = tags[-1] if tags else ''
        
        # Fetch suggestions based on the last tag
        suggestions = session.query(Tag.name).filter(Tag.name.like(f'{last_tag}%')).limit(10).all()
        suggestions = [suggestion[0] for suggestion in suggestions]  # Unpack tuples
        
        return {'suggestions': suggestions}
    
    return {'suggestions': []}

# Route to serve media files
@app.route('/media/<path:filename>')
def send_media(filename):
    directory = os.path.dirname(filename)  # Get the directory of the file
    return send_from_directory(directory, os.path.basename(filename))  # Use os.path.basename to get the filename

@app.route('/tag/<int:image_id>', methods=['GET', 'POST'])
def tag_media(image_id):
    # Fetch the media item
    media = session.query(Image).filter_by(id=image_id).first()
    
    if request.method == 'POST':
        # Get the tags and categories from the form input
        tags = request.form.get('tags', '').split(',')
        categories = request.form.get('categories', '').split(',')
        
        for tag_name, category in zip(tags, categories):
            tag_name = tag_name.strip()
            category = category.strip()  # Clean up the category

            # Find or create the tag
            tag = session.query(Tag).filter_by(name=tag_name).first()

            if not tag:
                # Create a new tag with the specified category if the tag doesn't exist
                tag = Tag(name=tag_name, category=category)
                session.add(tag)
            else:
                # Only update the category if a new category is provided (not an empty string)
                if category:
                    tag.category = category

            # Add the tag to the media
            if tag not in media.tags:
                media.tags.append(tag)

        session.commit()
        flash('Tags successfully added or updated!')

    # Sort tags by custom order: category first, then name alphabetically
    def tag_sort_key(tag):
        # Define custom category order: "site", "series", "actor", "meta", and then default (others)
        category_order = {
            'source': 0, #pinterest, instagram etc.
            'type': 1, #concept_art, screenshot etc.
            'author': 2, #author of the work
            'ip': 3, #what game, movie etc. its from
            'meta': 4, #video, photo etc.
            'element': 5 #UI, HUD, Options Menu etc.
        }
        # Default category rank is 6 if the category doesn't match the predefined ones
        category = tag.category.lower() if tag.category else ''

        # Default category rank is 6 if the category doesn't match the predefined ones
        category_rank = category_order.get(category, 6)

        # Return tuple (category rank, tag name in lowercase) for sorting
        return (category_rank, tag.name.lower())

    # Sort the tags before rendering
    sorted_tags = sorted(media.tags, key=tag_sort_key)

    # Get the previous and next media items for navigation
    previous_media = session.query(Image).filter(Image.id < image_id).order_by(Image.id.desc()).first()
    next_media = session.query(Image).filter(Image.id > image_id).order_by(Image.id).first()

    return render_template('tag.html', media=media, sorted_tags=sorted_tags, previous_media=previous_media, next_media=next_media)



@app.route('/update_tag_category', methods=['POST'])
def update_tag_category():
    tag_id = request.form.get('tag_id')
    category = request.form.get('category')

    # Find the tag by its ID
    tag = session.query(Tag).filter_by(id=tag_id).first()
    if tag:
        tag.category = category  # Update the category
        session.commit()
        flash(f'Category updated for tag "{tag.name}"!', 'success')
    else:
        flash('Tag not found!', 'error')

    return redirect(url_for('manage_tags'))

@app.route('/remove_tags/<int:image_id>', methods=['POST'])
def remove_tags(image_id):
    image = session.query(Image).filter_by(id=image_id).first()
    
    if image:
        tags_to_remove = request.form.get('tags_to_remove', '').split(',')
        for tag_name in tags_to_remove:
            tag_name = tag_name.strip()
            tag = session.query(Tag).filter_by(name=tag_name).first()
            if tag in image.tags:
                image.tags.remove(tag)
        session.commit()
        flash('Tags removed successfully.')

    return redirect(url_for('tag_media', image_id=image.id))

@app.route('/remove_tag_category', methods=['POST'])
def remove_tag_category():
    tag_id = request.form.get('tag_id')

    # Find the tag by its ID
    tag = session.query(Tag).filter_by(id=tag_id).first()
    if tag:
        tag.category = None  # Remove the category
        session.commit()
        flash(f'Category removed from tag "{tag.name}"!', 'success')
    else:
        flash('Tag not found!', 'error')

    return redirect(url_for('manage_tags'))

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)

    if query:
        tags = [tag.strip() for tag in query.split(',') if tag.strip()]
        
        # Use AND logic: Join by having conditions
        images = session.query(Image).join(Image.tags).filter(Tag.name.in_(tags)).group_by(Image.id).having(func.count(Tag.id) == len(tags)).order_by(Image.id.desc()).limit(ITEMS_PER_PAGE).offset((page - 1) * ITEMS_PER_PAGE).all()
        total_items = session.query(Image).join(Image.tags).filter(Tag.name.in_(tags)).group_by(Image.id).having(func.count(Tag.id) == len(tags)).count()
    else:
        images = session.query(Image).order_by(Image.id.desc()).limit(ITEMS_PER_PAGE).offset((page - 1) * ITEMS_PER_PAGE).all()
        total_items = session.query(Image).count()

    total_pages = math.ceil(total_items / ITEMS_PER_PAGE)

    # Ensure the category is included in the common_tags query
    common_tags = session.query(
    Tag.name, 
    Tag.category,  # Include the category
    func.count(Tag.id).label('count')
        ).join(Image.tags).group_by(Tag.name, Tag.category).order_by(func.count(Tag.id).desc()).all()



    return render_template('index.html', images=images, page=page, total_pages=total_pages, query=query, common_tags=common_tags)

# Route to delete an image or video from the database
@app.route('/delete/<int:image_id>', methods=['POST'])
def delete_media(image_id):
    image = session.query(Image).filter_by(id=image_id).first()

    if image:
        # Delete the image from the database only, keeping the file on disk
        session.delete(image)
        session.commit()
        flash('Media file deleted from database, but file remains on disk!')

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
