import PySimpleGUI as sg
import requests

from NewsPlayingModule.news import News
from NewsPlayingModule.newsPlayer import NewsPlayer
from NewsPlayingModule.userInterface import player_window


def load_initial_state(file_path : str):
	"""
	returns a list of strings, made of the lines of the given textual file
	"""
	ret = None
	with open(file_path, "r") as f:
		ret = f.readlines()
	ret = [el.replace("\n", "") for el in ret if el != "\n"]
	return ret

PASSENGERS_ONBOARD = load_initial_state("passengers_onboard.txt")

already_played_news = load_initial_state("already_played_news_links.txt")


news_player_obj = NewsPlayer(PASSENGERS_ONBOARD, already_played_news)


SERVER_BASE_URL = "http://localhost:5000"


WINDOW_WIDTH=700
WINDOW_HEIGHT=500

users_cached = None

def get_users_list(force_update = False):
	global users_cached
	if users_cached is not None and not force_update:
		return users_cached
	url = SERVER_BASE_URL + "/users"
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
	SERVER_ENDPOINT = SERVER_BASE_URL + "/speaker_profiles/"

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
		[sg.Column([
			[sg.Sizer(WINDOW_WIDTH,0)],
			[sg.Column([[sg.Button("Set current passengers", key="btn_get_users", expand_x=True)]], expand_x=True), sg.Sizer(WINDOW_WIDTH/2, 0), sg.Button("Start", key="btn_read_news", expand_x=True)]
			],
		element_justification="center")	#,expand_x=True, expand_y=True
		],
	[
		sg.Sizer(0,WINDOW_HEIGHT*0.82), 
			sg.Column([
				[sg.Column([], key="-USERS-LIST-")],
				[sg.Button("Save", key="btn_save_users_onboard", visible=False)]
				])
	],
	
	[sg.HorizontalSeparator("grey")],
	[sg.Text("Current passengers: " + ", ".join(PASSENGERS_ONBOARD),key="current_users", justification="left")]	#pad=((0,0), (20,0)), expand_y=True, vertical_alignment="bottom", 
]

#foo = sg.Column([], key="-USERS-LIST-")
#foo.
window = sg.Window("User List Window", layout, size=(WINDOW_WIDTH, WINDOW_HEIGHT))

#window.

#global user_list_layout
user_list_layout = []

#FOR TESTING ONLY
#news_to_play = {'Link': 'https://www.huffpost.com/entry/pop-tart-bowl-edible-mascot_n_658ef0abe4b0b01d3e3fce8b', 'Title': 'Fans Can’t Get Enough Of Pop-Tart Football Mascot Who Craved Being Eaten', 'Summary': 'Kansas State beat North Carolina State 28-19 in the Pop-Tart Bowl on Thursday. At the end of the game, the mascot was lowered into what appeared to be a giant toaster. The bottom of the toaster apparatus opened up and spit out a version of the mascot made out of edible Pop Tart material.', 'Article': 'College football got a little weirder than usual on Thursday during the Pop-Tart Bowl ― an annual December game that’s undergone numerous name changes over the past three decades. This year’s game,  in which Kansas State beat North Carolina State  28-19, involved a bug-eyed, human-sized Pop Tart mascot. Advertisement At the end of the game, the mascot brandished a sign reading, “DREAMS REALLY DO COME TRUE” before being lowered into what appeared to be a giant toaster. Donna Summer’s “Hot Stuff” blared in the background. The bottom of the toaster apparatus opened up and spit out a version of the mascot (with no human actor inside ― we hope) made out of edible Pop-Tart material. Kansas State players grabbed at the anthropomorphic Pop-Tart’s body and shoved bits of him into their mouths in a celebratory fashion. And some people highlighted the gruesome, jammy aftermath. Advertisement But don’t feel bad for the Pop-Tart. Reporter Rodger Sherman  confirmed with the mascot  prior to its toasty demise that the breakfast pastry indeed yearned to be eaten. Support HuffPost The Stakes Have Never Been Higher At HuffPost, we believe that everyone needs high-quality journalism, but we understand that not everyone can afford to pay for expensive news subscriptions. That is why we are committed to providing deeply reported, carefully fact-checked news that is freely accessible to everyone. Our Life, Health and Shopping desks provide you with well-researched, expert-vetted information you need to live your best life, while HuffPost Personal, Voices and Opinion center real stories from real people. At HuffPost, we believe that everyone needs high-quality journalism, but we understand that not everyone can afford to pay for expensive news subscriptions. That is why we are committed to providing deeply reported, carefully fact-checked news that is freely accessible to everyone. A vibrant democracy is impossible without well-informed citizens. We cannot do this without your help. At HuffPost, we believe that a vibrant democracy is impossible without well-informed citizens. This is why we keep our journalism free for everyone, even as most other newsrooms have retreated behind expensive paywalls. Our newsroom continues to bring you hard-hitting investigations, well-researched analysis and timely takes on one of the most consequential elections in recent history. Reporting on the current political climate is a responsibility we do not take lightly — and we need your help.', 'Date': '2023-12-29 17:51:54', 'Embedding': [0.0740853281, 0.9689050053, 0.0846071079, 0.1375558835, 0.172204736], 'Wav-link': None, 'wav_file_name': 'Fans-Cant-Get-Enough-Of-Pop-Tart-Football-Mascot-Who-Craved-Being-Eaten.wav'}
#wav_download_link = "Fans-Cant-Get-Enough-Of-Pop-Tart-Football-Mascot-Who-Craved-Being-Eaten.wav"
#news_obj = News(news_to_play, wav_download_link)
#player_window(news_obj)
#exit()
#END TESTING PART

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

	elif event == "btn_save_users_onboard":#"Save":
		print("previous passengers onboard: ", PASSENGERS_ONBOARD)
		print("Values: ", values)
		PASSENGERS_ONBOARD = []
		for user_infos in get_users_list():
			key = "checkbox_" + user_infos["username"]
			if key in values and values[key] == True:
				PASSENGERS_ONBOARD.append(user_infos["username"])

		window["-USERS-LIST-"].Update(visible=False)
		window["btn_save_users_onboard"].Update(visible=False)
		window["btn_get_users"].Update(visible=True)
		window["current_users"].Update("Current passengers: " + ", ".join(PASSENGERS_ONBOARD))

		download_vocal_profiles(PASSENGERS_ONBOARD)

		news_player_obj.update_passengers_list(PASSENGERS_ONBOARD)
		
		print("new passengers onboard: ", PASSENGERS_ONBOARD)

	elif event == "btn_read_news":
		# 1. send a request to the server endpoint for news suggestion
		#current_news = news_player_obj.get_next_news()

		# 2. call a method read_news(news_to_play : dict, wav_download_link : str) that plays the generated audio
		#	the best choice could be to show a new pyGUI window where the stop button, 
		#	the news text and (eventually) the image associated with the news is shown
		#	a. show a button to stop news reproduction
		#	b. text of the news
		#	c. image associated to the news
		# you should close this window only at the end of the session of usage, 
		# i.e. to stop the service or to change the list of passengers
		player_window(news_player_obj)

window.close()
