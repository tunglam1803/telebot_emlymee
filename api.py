import requests
from datetime import datetime
import pytz

def get_today_schedule():
    # Get current day in Vietnam (GMT+7)
    vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    now_vn = datetime.now(vn_tz)
    day_name = now_vn.strftime('%A').lower() # Monday, Tuesday, etc.
    
    url = f"https://api.jikan.moe/v4/schedules?filter={day_name}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        anime_list = []
        for item in data.get('data', []):
            # Jikan times are in JST (GMT+9) or provided as UTC
            # We'll just take the broadcast info for simplicity
            broadcast = item.get('broadcast', {})
            time_str = broadcast.get('time', 'N/A')
            
            anime_list.append({
                'id': item.get('mal_id'),
                'title': item.get('title'),
                'image': item.get('images', {}).get('jpg', {}).get('large_image_url'),
                'synopsis': item.get('synopsis'),
                'time': time_str,
                'day': day_name
            })
        return anime_list
    except Exception as e:
        print(f"Error fetching schedule: {e}")
        return []

def search_anime(query):
    url = f"https://api.jikan.moe/v4/anime?q={query}&limit=5"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get('data', []):
            results.append({
                'id': item.get('mal_id'),
                'title': item.get('title'),
                'image': item.get('images', {}).get('jpg', {}).get('large_image_url'),
                'airing_day': item.get('broadcast', {}).get('day', 'N/A'),
                'airing_time': item.get('broadcast', {}).get('time', 'N/A')
            })
        return results
    except Exception as e:
        print(f"Error searching anime: {e}")
        return []

if __name__ == "__main__":
    # Test
    print("Searching for 'One Piece'...")
    results = search_anime("One Piece")
    for r in results:
        print(f"- {r['title']} (ID: {r['id']})")
