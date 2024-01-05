import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO

def get_thumbnail_url(url, min_width=100, min_height=100):
    try:
        # Fetch webpage content
        response = requests.get(url)
        if response.status_code == 200:
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all image tags
            images = soup.find_all('img')
            
            for img in images:
                if img.has_attr('src'):
                    thumbnail_url = img['src']
                    # Fetch image content
                    img_response = requests.get(thumbnail_url)
                    if img_response.status_code == 200:
                        # Open image using PIL/Pillow
                        img_data = BytesIO(img_response.content)
                        img_pil = Image.open(img_data)
                        
                        # Check image dimensions
                        img_width, img_height = img_pil.size
                        if img_width >= min_width and img_height >= min_height:
                            return thumbnail_url
            return "No thumbnail found with specified size"
        else:
            return "Failed to fetch webpage"
    except requests.RequestException as e:
        return f"Error: {e}"