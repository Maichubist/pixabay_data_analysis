import pandas as pd

from db.database import SessionLocal
from db.model_user import Users
from db.model_image_type import ImageTypes
from db.model_image_fact import ImageFacts
from db.model_tag import Tags

from db.database import Base, engine
Base.metadata.create_all(engine)

class DB:
    def __init__(self):
        self.db = SessionLocal()

    def load_data(self, df):
        try:
            for index, row in df.iterrows():
                tags = [tag.strip() for tag in row['tags'].split(',')]
                if len(tags) != 3:
                    raise ValueError("Each row must have exactly three tags")

                tag_objects = []
                for tag_name in tags:
                    tag = self.db.query(Tags).filter(Tags.tag == tag_name).first()
                    if not tag:
                        tag = Tags(tag=tag_name)
                        self.db.add(tag)
                        self.db.commit()
                    tag_objects.append(tag)
                
                user = self.db.query(Users).filter(Users.user == row['user']).first()
                if not user:
                    user = Users(user=row['user'], userImageURL=row['userImageURL'])
                    self.db.add(user)
                    self.db.commit()
                
                image_type = self.db.query(ImageTypes).filter(ImageTypes.type == row['type']).first()
                if not image_type:
                    image_type = ImageTypes(type=row['type'])
                    self.db.add(image_type)
                    self.db.commit()
                
                image_fact = ImageFacts(
                    user_id=user.user_id, type_id=image_type.type_id, 
                    tag1_id=tag_objects[0].tag_id, 
                    tag2_id=tag_objects[1].tag_id, 
                    tag3_id=tag_objects[2].tag_id,
                    views=row['views'], downloads=row['downloads'], collections=row['downloads'], 
                    likes=row['likes'], comments=row['comments'], imageWidth=row['imageWidth'], 
                    imageHeight=row['imageHeight'], imageSize=row['imageSize'], 
                    largeImageURL=row['largeImageURL'], pageURL=row['pageURL']
                )
                self.db.add(image_fact)
            
            self.db.commit()
        
        except Exception as e:
            self.db.rollback()
            raise e
        
        finally:
            self.db.close()

    def load_data_into_df(self):
        self.db = SessionLocal()
        try:
            query = self.db.query(Users, ImageTypes, ImageFacts, Tags).\
                join(ImageFacts, Users.user_id == ImageFacts.user_id).\
                join(ImageTypes, ImageFacts.type_id == ImageTypes.type_id).\
                join(Tags, Tags.tag_id.in_([ImageFacts.tag1_id, ImageFacts.tag2_id, ImageFacts.tag3_id]))

            # Group the tags by image fact
            from collections import defaultdict
            grouped_tags = defaultdict(list)
            for user, image_type, image_fact, tag in query:
                grouped_tags[image_fact.id].append(tag)

            data = []
            processed_image_facts = set()  # Keep track of processed image facts to avoid duplication
            for user, image_type, image_fact, _ in query:
                if image_fact.id not in processed_image_facts:
                    # Combine the tags for each image fact into a single string
                    tag_str = ", ".join([tag.tag for tag in grouped_tags[image_fact.id]])
                    data.append({
                        'user': user.user,
                        'userImageURL': user.userImageURL,
                        'type': image_type.type,
                        'views': image_fact.views,
                        'downloads': image_fact.downloads,
                        'collections': image_fact.collections,
                        'likes': image_fact.likes,
                        'comments': image_fact.comments,
                        'imageWidth': image_fact.imageWidth,
                        'imageHeight': image_fact.imageHeight,
                        'imageSize': image_fact.imageSize,
                        'largeImageURL': image_fact.largeImageURL,
                        'pageURL': image_fact.pageURL,
                        'tags': tag_str
                    })
                    processed_image_facts.add(image_fact.id)

            return pd.DataFrame(data)

        finally:
            self.db.close()


db = DB()


