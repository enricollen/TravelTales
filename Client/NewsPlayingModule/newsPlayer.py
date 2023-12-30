from NewsPlayingModule.news import News

import requests

SERVER_BASE_URL = "http://localhost:5000"

class NewsPlayer:
    def __init__(self, passengers_list : list, already_played_news : list = []) -> None:
        
        self.passengers = passengers_list

        self.__already_played_news = already_played_news
        self.__news_index = -1
        pass

    def update_passengers_list(self, passenger_list):
        """
        this method has to be called after that the list of passengers is modified
        it requests to the server the updated list of news to suggest, so that they fit with the currently logged-in users
        """
        self.passengers = passenger_list
        self.fetch_suggested_news()

    def get_next_news(self, check_if_already_played=True) -> News:
        if hasattr(self, "cached") and self.cached is not None:
            news_list = self.cached 
        else:
            #print(f"hasattr(self, 'cached'): {hasattr(self, 'cached')}")
            #if hasattr(self, 'cached'):
            #    print(f"self.cached is not None: {self.cached is not None}")
            #    print(f"self.cached: {self.cached}")
            news_list = self.fetch_suggested_news()

        #if self.__news_index == -1:
        #    self.__news_index = 0
        initial = self.__news_index

        if self.__news_index == len(news_list) - 1:
            print(f"Rewinding news_list since the end was reached")
            self.__news_index = -1
        
        for self.__news_index in range(self.__news_index+1, len(news_list)):
            news_to_play = news_list[self.__news_index]
            news_link = news_to_play["Link"]
            if news_link in self.__already_played_news and check_if_already_played:
                print("Skipping already played news")
                #if self.__news_index == len(news_list):
                #    self.__news_index = 0
                #    TODO: a logic that handles when all the news were already played and fetches new news
                continue
            
            if "Wav-link" in news_to_play.keys() and news_to_play["Wav-link"] != None:
                wav_download_link = news_to_play["Wav-link"]

            elif "wav_file_name" in news_to_play.keys() and news_to_play["wav_file_name"] != None:
                wav_download_link = SERVER_BASE_URL + "/audio-news/" + news_to_play["wav_file_name"]
            else:
                print("Skipping news without audio trace")
                continue
            break

        self.__current_news = News(news_to_play, wav_download_link)

        #print(f"[DEBUG]: initial: {initial}\t after the loop: {self.__news_index}")
        return self.__current_news
    
    def get_current_news(self) -> News:
        if hasattr(self, "__current_news") and self.__current_news is not None:
            return self.__current_news
        print("Loading next news, since no news currently loaded")
        return self.get_next_news()
    
    def get_previous_news(self) -> News:
        """
        returns the News object associated to the previous news if any, else returns None
        """
        if self.__news_index > 0:
            news_list = self.cached
            for self.__news_index in range(self.__news_index - 1, -1, -1):
                news_to_play = news_list[self.__news_index]
                                
                if "Wav-link" in news_to_play.keys() and news_to_play["Wav-link"] != None:
                    wav_download_link = news_to_play["Wav-link"]

                elif "wav_file_name" in news_to_play.keys() and news_to_play["wav_file_name"] != None:
                    wav_download_link = SERVER_BASE_URL + "/audio-news/" + news_to_play["wav_file_name"]
                else:
                    print("Skipping news without audio trace")
                    continue
                break

            self.__current_news = News(news_to_play, wav_download_link)
            return self.__current_news
            
        else:
            return None
        
    

    def add_news_to_played(self, news : News):
        """
        adds the given news to the list of already played news
        call this method after that the news was played by the system
        """
        if news.get_news_link() in self.__already_played_news:
            print(f"[!] Warning calling add_news_to_played on a news already added [!] Title: {news.get_title()}")
            return
        
        self.__already_played_news.append(news.get_news_link())

    	
    def fetch_suggested_news(self):
        """
        returns the list of suggested news from the system,
        it caches them for disconnection tolerance
        the fields in each element of the list are:
        - Link
        - Title
        - Summary
        - Article
        - Date
        - Embedding
        - Wav-link
        - wav_file_name
        """
        print("Fetching news from the server...", end="")
        endpoint= SERVER_BASE_URL + f"/news_suggestion?users={';'.join(self.passengers)}"
        try:
            response = requests.get(endpoint)
            response.raise_for_status()
            self.cached = response.json()
            self.__news_index = -1
            self.__current_news = None
            print("Done!")
            return self.cached
        except Exception as e:
            print(e)
            print("[!] CANNOT FETCH NEWS FROM THE SERVER [!]")
            if hasattr(self, "cached") and self.cached is not None:
                print("[-] RETURNING LOCALLY CACHED SET OF NEWS [-]")
                return self.cached
            return None
        