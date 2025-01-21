from sqlalchemy import create_engine, Column, String, Integer, Table, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

image_tag_table = Table('image_tag', Base.metadata,
    Column('image_id', Integer, ForeignKey('images.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

class Image(Base):
    __tablename__ = 'images'
    
    id = Column(Integer, primary_key=True)
    path = Column(String, unique=True)
    tags = relationship('Tag', secondary=image_tag_table, back_populates='images')

class Tag(Base):
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    category = Column(String)  # New category field
    images = relationship('Image', secondary=image_tag_table, back_populates='tags')

def init_db(db_path='sqlite:///booru.db'):
    engine = create_engine(db_path)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

    
Session = init_db()
