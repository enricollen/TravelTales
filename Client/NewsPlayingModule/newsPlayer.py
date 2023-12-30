"""
This class handles the window dedicated to the audio reproduction of a given news
it has to show in the window:
- the text of the news
- play / pause button to stop news reproduction
- (opt) the title of the news
- (opt) the image associated with the news

When its window is closed, it has to stop news reproduction.

TODO: write down if it has to handle also feedback gathering inside this window
"""
import os
import requests
from datetime import datetime

#SERVER_BASE_URL = "http://localhost:5000"

class NewsPlayer:
    def __init__(self, news_dict : dict, wav_download_link : str) -> None:
        self.news_dict = news_dict
        self.wav_link = wav_download_link
        self.__fetch_wav()
        
    def get_news_image_path(self):
        return ""
    
    def get_title(self):
        return self.news_dict["Title"]
    
    def get_wav_local_path(self):
        return self.wavlocalpath

    def __fetch_wav(self):
        """
        downloads the updated vocal profiles for the given list of usernames.
        If a newer profile is available on the server, downloads the updated version, otherwhise keeps the local one without redownloading
        """
        OUTPUT_DIR ="audio-news"
        remote_url = self.wav_link
        filename = remote_url.split("/")[-1]
        self.wavlocalpath = localpath = os.path.join(OUTPUT_DIR, filename)

        if os.path.exists(localpath):
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
        