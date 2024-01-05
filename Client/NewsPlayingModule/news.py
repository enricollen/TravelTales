import os
import requests
from datetime import datetime
from PIL import Image
from io import BytesIO
import numpy as np

from bs4 import BeautifulSoup

def crop_to_dimensions(img : Image, target_width, target_height):
    width, height = img.size
    left = (width - target_width) / 2
    top = (height - target_height) / 2
    right = (width + target_width) / 2
    bottom = (height + target_height) / 2
    cropped_img = img.crop((left, top, right, bottom))
    return cropped_img

#SERVER_BASE_URL = "http://localhost:5000"

class News:
    """
    This class exposes the getters method to fetch wav, png and txt files associated to a news
    """

    CATEGORIES = ['business', 'entertainment', 'politics', 'sport', 'tech']
    COLORS = ["blue", "green", "yellow", "orange", "purple", "brown"]
    COLOR_INDEX = 0

    def __init__(self, news_dict : dict, wav_download_link : str) -> None:
        self.news_dict = news_dict
        self.wav_link = wav_download_link
        self.color = News.COLORS[::-1][News.COLOR_INDEX]
        News.COLOR_INDEX = (News.COLOR_INDEX + 1) % len(News.COLORS)
        self.__fetch_wav()
        
    def get_news_image_link(self):
        """
        TODO
        """
        min_width = 200
        min_height = 200
        try:
            # Fetch webpage content
            response = requests.get(self.get_news_link())
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
                return None
            else:
                return None
        except requests.RequestException as e:
            print(f"Error: {e}")
            return None
        #import random
        #token_images_set = [
        #    "https://img.iltempo.it/images/2023/12/23/094850031-fc81569b-98ee-4004-975f-6a5dc5d34b48.jpg",
        #    "https://media-assets.wired.it/photos/615d7cea47dec6c387f9776d/master/w_1600%2Cc_limit/wired_placeholder_dummy.png",
        #    "https://www.gedistatic.it/content/gnn/img/lastampa/2023/04/05/122323695-d7e1ee28-b6e9-4ce9-88e5-ce79823f1021.jpg",
        #    "https://st.ilfattoquotidiano.it/wp-content/uploads/2023/07/13/matteo-renzi-3-690x362.jpg",
        #    "https://img.ilgcdn.com/sites/default/files/styles/md/public/foto/2022/02/09/1644440349-3dc46de61eddef823b2fab3362e0d577.jpg",
        #    "https://static.ilmanifesto.it/2023/12/27lettere2-matteo-renzi-lapresse.jpg",
        #    "https://assets.nationbuilder.com/comitaticivici/pages/12778/meta_images/original/Imagoeconomica_1985936.jpg"  
        #]
        #return token_images_set[random.randint(0, len(token_images_set)-1)]
    
    def get_news_image_local_path(self, target_width=350, target_height=350, use_category_pic=False):
        """
        returns the local path to the image associated with this news
        the image is in png format and is cropped to the specified width and height
        """
        IMG_DIR = "news-images/"

        remote_url = self.get_news_image_link()

        if remote_url is None or use_category_pic is True:
            return self.get_news_category_image()
        
        filename = remote_url.split("/")[-1]

        filename = filename.split("?")[0]

        output_path = os.path.join(IMG_DIR, filename)

        if os.path.exists(output_path):
            print(f"Image already downloaded, returning local path for {filename}")
            return output_path
        
        # if the image is not already present, will download it

        try:
            # Send a GET request to download the image
            response = requests.get(remote_url)
            
            if response.status_code == 200:
                # Open the image using PIL
                img = Image.open(BytesIO(response.content))
                
                # Convert the image to PNG format
                img = img.convert("RGB")
                
                # Crop the image to specific dimensions
                img = crop_to_dimensions(img, target_width, target_height)
                
                # Save the image to the specified output path
                img.save(output_path, format="png")
                
                return output_path
            else:
                print("Failed to download the image. Status code:", response.status_code)
                print(f"Download url {remote_url}")
                return None
        except Exception as e:
            print("An error occurred:", str(e))
            return None
    
    def get_news_category_image(self):
        """
        returns the local path to the image associated with this category
        """
        category_id = np.argmax(self.news_dict['Embedding'])
        category = self.CATEGORIES[category_id]
        IMG_DIR = "news-images/"
        filename = category + ".png"

        output_path = os.path.join(IMG_DIR, filename)
        return output_path
        
    
    def get_title(self):
        return self.news_dict["Title"]
    
    def get_summary(self):
        return self.news_dict["Summary"]
    
    def get_news_link(self):
        return self.news_dict["Link"]
    
    def get_embedding(self):
        ret = self.news_dict["Embedding"]
        #print(f"get_embedding on news; returning : {ret}\t type: {type(ret)}")
        return ret
    
    def get_color(self):
        return self.color
    
    def get_wav_local_path(self):
        return self.wavlocalpath

    def __fetch_wav(self, check_for_updates=False):
        """
        downloads the updated vocal profiles for the given list of usernames.
        If a newer profile is available on the server, downloads the updated version, otherwhise keeps the local one without redownloading
        """
        OUTPUT_DIR ="audio-news"
        remote_url = self.wav_link
        filename = remote_url.split("/")[-1]
        self.wavlocalpath = localpath = os.path.join(OUTPUT_DIR, filename)

        if os.path.exists(localpath):

            if not check_for_updates:
                return 

            local_last_modified = os.path.getmtime(localpath)
            response = requests.head(remote_url)

            if response.status_code == 200:
                remote_last_modified = response.headers.get("Last-Modified")

                if remote_last_modified:
                    remote_last_modified = float(datetime.strptime(remote_last_modified, "%a, %d %b %Y %H:%M:%S %Z").timestamp())
                    if remote_last_modified <= local_last_modified:
                        print(f"The local version of audio-news for {filename} does not need an update")
                        return
        
        # if we arrive here, we have to download the updated version of the audio news
        try:		
            response = requests.get(remote_url)
            
            if response.status_code == 200:
                os.makedirs(os.path.dirname(localpath), exist_ok=True)
                with open(localpath, "wb") as output_file:
                    output_file.write(response.content)
                    print(f"Downloaded newer audio news {filename}")
        except Exception as e:
            print(e)
            print(f"An error occurred while downloading audio news {filename}")
        
        # when i am here, i have the audio news file locally at 'localpath'
        