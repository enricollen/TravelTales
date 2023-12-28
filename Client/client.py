import PySimpleGUI as sg
import requests

PASSENGERS_ONBOARD = []

users_cached = None

def get_users_list(force_update = False):
	global users_cached
	if users_cached is not None and not force_update:
		return users_cached
	url = "http://localhost:5000/users"
	try:
		response = requests.get(url)
		response.raise_for_status()  # Raise an exception for HTTP errors (4xx, 5xx)
		users_data = response.json()
		users_cached = users_data
		return users_data
	except requests.RequestException as e:
		sg.popup_error(f"Error retrieving user list: {e}")
		return []

import os
from datetime import datetime

def download_vocal_profiles(list_of_usernames : list):
	"""
	downloads the updated vocal profiles for the given list of usernames.
	If a newer profile is available on the server, downloads the updated version, otherwhise keeps the local one without redownloading
	"""
	OUTPUT_DIR ="speaker_profiles"
	SERVER_ENDPOINT = "http://localhost:5000/speaker_profiles/"

	for username in list_of_usernames:
		filename = f"{username}.pv"
		localpath = os.path.join(OUTPUT_DIR, filename)
		remote_url = SERVER_ENDPOINT + filename
		if os.path.exists(localpath):
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

layout = [
	[sg.Button("Get Users List", key="btn_get_users")],
	[sg.Column([], key="-USERS-LIST-")],#[sg.Checkbox(user["username"], key=f"checkbox_{user['username']}") for user in get_users_list()],
	[sg.Button("Save", key="btn_save_users_onboard", visible=False)],
	[sg.HorizontalSeparator("grey")],
	[sg.Text("Current users: ",key="current_users", pad=((0,0), (20,0)), justification="left", expand_y=True)]	#vertical_alignment="bottom", 
]

#foo = sg.Column([], key="-USERS-LIST-")
#foo.
window = sg.Window("User List Window", layout, size=(700, 500))

#window.

#global user_list_layout
user_list_layout = []

while True:
	event, values = window.read()

	if event == sg.WIN_CLOSED:
		break
	elif event == "btn_get_users":#"Get Users List":
		#global user_list_layout
		user_list_layout = [
			[sg.Checkbox(user["username"], key=f"checkbox_{user['username']}")] for user in get_users_list(force_update=True) if f"checkbox_{user['username']}" not in values.keys()
		]
		window.extend_layout(window["-USERS-LIST-"], user_list_layout)
		window["btn_get_users"].Update(visible=False)
		window["btn_save_users_onboard"].Update(visible=True)
		window["-USERS-LIST-"].Update(visible=True)
		#window
		#window["-USERS-LIST-"].update(user_list_layout)
	elif event == "btn_save_users_onboard":#"Save":
		print("previous passengers onboard: ", PASSENGERS_ONBOARD)
		print("Values: ", values)
		PASSENGERS_ONBOARD = []
		for user_infos in get_users_list():
			key = "checkbox_" + user_infos["username"]
			if key in values and values[key] == True:
				PASSENGERS_ONBOARD.append(user_infos["username"])
		#print("window[\"-USER_LIST-\"]", window["-USERS-LIST-"])
		window["-USERS-LIST-"].Update(visible=False)
		window["btn_save_users_onboard"].Update(visible=False)
		window["btn_get_users"].Update(visible=True)
		window["current_users"].Update("Current passengers: " + " ".join(PASSENGERS_ONBOARD))
		#PASSENGERS_ONBOARD=[x.Text for x in window["-USERS-LIST-"] if x.get()==True]
		download_vocal_profiles(PASSENGERS_ONBOARD)
		print("new passengers onboard: ", PASSENGERS_ONBOARD)

window.close()