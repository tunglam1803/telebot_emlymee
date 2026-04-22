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
        broadcast = item.get('broadcast', {})
        jst_time = broadcast.get('time', 'N/A')
        
        vn_time = jst_time
        if jst_time != 'N/A':
            try:
                hour, minute = map(int, jst_time.split(':'))
                hour_vn = (hour - 2) % 24
                vn_time = f"{hour_vn:02d}:{minute:02d}"
            except:
                pass
        
        anime_list.append({
            'id': item.get('mal_id'),
            'title': item.get('title'),
            'image': item.get('images', {}).get('jpg', {}).get('large_image_url'),
            'synopsis': item.get('synopsis'),
            'time': vn_time,
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
def get_anime_by_id(mal_id):
    url = f"https://api.jikan.moe/v4/anime/{mal_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        item = response.json().get('data', {})
        
        broadcast = item.get('broadcast', {})
        jst_day = broadcast.get('day', 'N/A')
        jst_time = broadcast.get('time', 'N/A')
        
        vn_day = jst_day
        vn_time = jst_time
        
        # Chuyển đổi từ JST (GMT+9) sang VN (GMT+7): Trừ 2 tiếng
        if jst_time != 'N/A':
            try:
                hour, minute = map(int, jst_time.split(':'))
                hour_vn = hour - 2
                
                if hour_vn < 0:
                    hour_vn += 24
                    # Lùi 1 ngày nếu giờ VN bị quay về ngày trước
                    days = ["Mondays", "Tuesdays", "Wednesdays", "Thursdays", "Fridays", "Saturdays", "Sundays"]
                    if jst_day in days:
                        idx = (days.index(jst_day) - 1) % 7
                        vn_day = days[idx]
                
                vn_time = f"{hour_vn:02d}:{minute:02d}"
            except:
                pass
                
        # Dịch sang tiếng Việt
        day_map = {
            "Mondays": "Thứ Hai", "Tuesdays": "Thứ Ba", "Wednesdays": "Thứ Tư",
            "Thursdays": "Thứ Năm", "Fridays": "Thứ Sáu", "Saturdays": "Thứ Bảy",
            "Sundays": "Chủ Nhật", "N/A": "Chưa rõ"
        }
        
        return {
            'id': item.get('mal_id'),
            'title': item.get('title'),
            'airing_day': day_map.get(vn_day, vn_day),
            'airing_time': vn_time
        }
    except Exception as e:
        print(f"Error fetching anime detail: {e}")
        return None

if __name__ == "__main__":
    # Test
    print("Searching for 'One Piece'...")
    results = search_anime("One Piece")
    for r in results:
        print(f"- {r['title']} (ID: {r['id']})")
