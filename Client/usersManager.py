from dotenv import load_dotenv
import requests
import os
from datetime import datetime
from user import User

load_dotenv()

VOCAL_PROFILES_OUTPUT_DIR = os.getenv("VOCAL_PROFILES_OUTPUT_DIR")
SERVER_BASE_URL = os.getenv("SERVER_BASE_URL")

class UsersManager:

    users_cached = None

    def __init__(self, passengers_onboard : list[str]) -> None:
        self.set_passengers_list(passengers_onboard)

    def get_passengers_usernames(self) -> list[str]:
        """
        - returns the list of the usernames of the passengers onboard
        """
        return self.PASSENGERS_ONBOARD
    
    def set_passengers_list(self, PASSENGERS_ONBOARD : list[str]):
        self.PASSENGERS_ONBOARD = PASSENGERS_ONBOARD
        self.PASSENGERS_OBJS = []
        
        users_list = UsersManager.get_users_list(False)

        for user_row in users_list:
            username = user_row['username']
            if (username not in self.PASSENGERS_ONBOARD):
                continue
            user = User(username, user_row['interests'], os.path.join(VOCAL_PROFILES_OUTPUT_DIR, f'{username}.pv'))
            self.PASSENGERS_OBJS.append(user)
        
        self.download_vocal_profiles()


    def get_passengers_objs(self) -> list[User]:
        return self.PASSENGERS_OBJS

    def get_users_list(force_update = False):
        """
        fetches the list of users from the server, or returns the cached list if is present
        the field of each element of the list are:
        - username
        - interests
        """
        
        if UsersManager.users_cached is not None and not force_update:
            return UsersManager.users_cached
        url = SERVER_BASE_URL + "/users"
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx, 5xx)
            users_data = response.json()
            UsersManager.users_cached = users_data
            return users_data
        except requests.RequestException as e:
            print(f"Error retrieving user list: {e}")
            return []
        

    def download_vocal_profiles(self, list_of_usernames : list = [], check_for_updates=False):
        """
        downloads the updated vocal profiles for the given list of usernames.
        If a newer profile is available on the server, downloads the updated version, otherwhise keeps the local one without redownloading
        """
        SERVER_ENDPOINT = SERVER_BASE_URL + "/speaker_profiles/"

        if list_of_usernames is None or len(list_of_usernames) == 0:
            list_of_usernames = self.PASSENGERS_ONBOARD

        for username in list_of_usernames:
            filename = f"{username}.pv"
            localpath = os.path.join(VOCAL_PROFILES_OUTPUT_DIR, filename)
            remote_url = SERVER_ENDPOINT + filename
            if os.path.exists(localpath):

                if check_for_updates is False:
                    print(f"A local copy of the voice profile for {username} is available, skipping updates")
                    continue

                local_last_modified = os.path.getmtime(localpath)
                response = requests.head(remote_url)

                if response.status_code == 200:
                    remote_last_modified = response.headers.get("Last-Modified")

                    if remote_last_modified:
                        remote_last_modified = float(datetime.strptime(remote_last_modified, "%a, %d %b %Y %H:%M:%S %Z").timestamp())
                        if remote_last_modified <= local_last_modified:
                            print(f"The local version of voice profile for {username} does not need an update")
                            continue
            
            # if we arrive here, we have to download the updated version of voice profile
            try:		
                response = requests.get(remote_url)
                
                if response.status_code == 200:
                    os.makedirs(os.path.dirname(localpath), exist_ok=True)
                    with open(localpath, "wb") as output_file:
                        output_file.write(response.content)
                        print(f"Downloaded newer voice profile for user {username}")
            except Exception as e:
                print(e)
                print(f"An error occurred while downloading voice profile for {username}")