import os
import psycopg2
import psycopg2.extras
import googleapiclient.discovery
from datetime import datetime
import json

API_KEY = os.getenv("API_KEY", "AIzaSyBAnDCX6u1ya5cHQQzN9rQdn43ECzr3pvY")
DB_PARAMS = {
    'dbname': os.getenv("DB_NAME", "postgres"),
    'user': os.getenv("DB_USER", "postgres"),
    'password': os.getenv("DB_PASSWORD", "Nokia_2730"),
    'host': os.getenv("DB_HOST", "postgres"),  
    'port': os.getenv("DB_PORT", "5432")
}

def create_activities_table():
    create_table_query = """
    CREATE TABLE IF NOT EXISTS activities (
        activity_id VARCHAR(255) PRIMARY KEY,
        published_at TIMESTAMP,
        channel_id VARCHAR(255),
        title VARCHAR(255),
        description TEXT,
        thumbnails JSON,
        channel_title VARCHAR(255),
        type VARCHAR(255),
        content_details JSON
    );
    """
    try:
        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute(create_table_query)
            conn.commit()
        print("Table 'activities' is ready.")
    except Exception as e:
        print(f"Database ERROR: {e}")

def get_channel_activities(channel_id, max_results=100):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=API_KEY)
    activities = []
    next_page_token = None

    while True:
        try:
            request = youtube.activities().list(
                part="snippet,contentDetails",
                channelId=channel_id,
                maxResults=max_results,
                pageToken=next_page_token
            )
            response = request.execute()

            for item in response['items']:
                snippet = item.get('snippet', {})
                activity = {
                    "id": item['id'],
                    "published_at": snippet.get('publishedAt'),
                    "channel_id": snippet.get('channelId'),
                    "title": snippet.get('title', ''),
                    "description": snippet.get('description', ''),
                    "thumbnails": json.dumps(snippet.get('thumbnails', {})),
                    "channel_title": snippet.get('channelTitle', ''),
                    "type": snippet.get('type', ''),
                    "content_details": json.dumps(item.get('contentDetails', {}))
                }
                activities.append(activity)

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        except Exception as e:
            print(f"An error occurred: {e}")
            break
    return activities

def insert_activities_to_postgres(activities):
    insert_query = """
    INSERT INTO activities (activity_id, published_at, channel_id, title, description, thumbnails, channel_title, type, content_details)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                psycopg2.extras.execute_batch(
                    cur,
                    insert_query,
                    [(activity['id'],
                      activity['published_at'],
                      activity['channel_id'],
                      activity['title'],
                      activity['description'],
                      activity['thumbnails'],
                      activity['channel_title'],
                      activity['type'],
                      activity['content_details']) for activity in activities],
                    page_size=100  
                )
            conn.commit()
        print(f"Successfully inserted {len(activities)} records into the database.")
    except Exception as e:
        print(f"Database ERROR: {e}")

def main():
    channel_id = "UCQ0jSGgYMLmRMeTE6UaPPXg"
    create_activities_table() 
    activities = get_channel_activities(channel_id)

    if activities:
        insert_activities_to_postgres(activities)

if __name__ == "__main__":
    main()
