from pymongo import MongoClient
import cv2
import base64
from datetime import datetime
import os

class DatabaseHelper:
    def __init__(self):
        self.client = MongoClient('mongodb+srv://saikiransuguru:7eYEmWV5Nmzrn24m@cluster0.sbi4o.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0/')
        self.db = self.client['face_recognition']
        self.users_collection = self.db['users']  # New collection for user data
        self.encodings_collection = self.db['face_encodings']

    def save_image(self, frame, name):
        """Save image and update user's timestamp log"""
        now = datetime.now()
        
        # Convert image to base64
        _, buffer = cv2.imencode('.jpg', frame)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Create image name
        image_name = f"{name}_{now.strftime('%Y%m%d_%H%M%S')}.jpg"

        # Update or create user document with new timestamp and image
        self.users_collection.update_one(
            {'name': name},
            {
                '$push': {
                    'timestamps': now,
                    'images': {
                        'image_name': image_name,
                        'image_data': img_base64,
                        'timestamp': now
                    }
                }
            },
            upsert=True
        )

        return image_name

    def save_face_encoding(self, encoding, name):
        """Save face encoding to MongoDB"""
        encoding_doc = {
            'name': name,
            'encoding': encoding.tolist(),
            'timestamp': datetime.now()
        }
        self.encodings_collection.insert_one(encoding_doc)

    def get_all_encodings(self):
        """Get all face encodings from MongoDB"""
        encodings_docs = list(self.encodings_collection.find())
        if not encodings_docs:
            return {'encodings': [], 'names': []}
        
        return {
            'encodings': [doc['encoding'] for doc in encodings_docs],
            'names': [doc['name'] for doc in encodings_docs]
        }

    def get_user_history(self, name):
        """Get user's visit history"""
        user = self.users_collection.find_one({'name': name})
        if user:
            return {
                'name': name,
                'visit_count': len(user.get('timestamps', [])),
                'timestamps': user.get('timestamps', [])
            }
        return None
    
    def get_all_users_history(self):
        users = self.users_collection.find()
        result = []
        for user in users:
            result.append({
                'name': user['name'],
                'visit_count': len(user.get('timestamps', [])),
                'timestamps': [ts.strftime('%m/%d/%Y, %I:%M:%S %p') for ts in user.get('timestamps', [])],
                'images': user.get('images', [])
            })
        return result

    def get_latest_image(self, name):
        """Get user's most recent image"""
        user = self.users_collection.find_one(
            {'name': name},
            {'images': {'$slice': -1}}  # Get only the latest image
        )
        if user and user.get('images'):
            return user['images'][0]
        return None

    def get_image(self, image_name):
        """Retrieve image from MongoDB"""
        image_doc = self.users_collection.find_one(
            {'images.image_name': image_name},
            {'images.$': 1}  # Retrieve the specific image
        )
        if image_doc and image_doc.get('images'):
            return base64.b64decode(image_doc['images'][0]['image_data'])
        return None

    def clear_all_data(self):
        """Clear all data from MongoDB only"""
        self.users_collection.delete_many({})
        self.encodings_collection.delete_many({})