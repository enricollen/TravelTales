import PySimpleGUI as sg
import os
import textwrap

from NewsPlayingModule.utils.music_utilities import MusicUtilites #play_sound, is_sound_playing, pause_sounds, stop_sounds, unpause

from NewsPlayingModule.news import News
from NewsPlayingModule.newsPlayer import NewsPlayer
from usersManager import UsersManager

from DataVisualizationModule.userInterface import data_visualization_window

WINDOW_WIDTH = 700
WINDOW_HEIGHT = 580

MUSIC_FOLDER = "audio-music"

"""
This class handles the window dedicated to the audio reproduction of a given news
it has to show in the window:
- the text of the news
- play / pause button to stop news reproduction
- the title of the news
- the image associated with the news

When its window is closed, it has to stop news reproduction.

TODO: decide if it has to handle also feedback gathering inside this window
    I think it would be the best choice

TODO: add elevator music in the background eventually
"""

def player_window(news_player_obj : NewsPlayer, users_manager_obj : UsersManager):

    current_news_obj = news_player_obj.get_current_news()

    DEFAULT_IMAGE_PATH = 'NewsPlayingModule\\Images\\travel-tales.png'   #news_player_obj.get_news_image_path()


    sg.theme('Reddit')
    song_title_column = [
        [sg.Text(text='Press play to read news', justification='center', background_color='black',
                text_color='white', size=(200, 0), font='Tahoma', key='song_name')]
    ]

    player_info = [
        [sg.Text('TravelTales Player'
                , background_color='black', text_color='white',  font=('Tahoma', 7))]  #
    ]

    currently_playing = [
        [sg.Text(background_color='black', size=(200, 0), text_color='white',
                font=('Tahoma', 10), key='currently_playing')]
    ]

    GO_BACK_IMAGE_PATH = 'NewsPlayingModule\\Images\\back.png'
    GO_FORWARD_IMAGE_PATH = 'NewsPlayingModule\\Images\\next.png'
    PLAY_SONG_IMAGE_PATH = 'NewsPlayingModule\\Images\\play_button.png'
    PAUSE_SONG_IMAGE_PATH = 'NewsPlayingModule\\Images\\pause.png'


    main = [
        
        [sg.Column(layout=player_info, justification='c',
                element_justification='c', background_color='black')],
        [
            
            sg.Image(filename=DEFAULT_IMAGE_PATH,
                    size=(350, 350), pad=None, key="news_image"),
            sg.Text("News summary", key="news_summary", background_color="black", text_color="white", font=('Tahoma', 10), expand_x=True, justification="center")
            
        ],
        [sg.Column([
			[sg.Sizer(WINDOW_WIDTH,0)],
			[
                sg.Button("Show plots", key="btn_show_plots", expand_x=True),
                sg.Sizer(WINDOW_WIDTH/3, 0), 
                sg.Button("Start listening", key="btn_feedback_gathering", expand_x=True)]
			],
            element_justification="center", background_color="black")	#,expand_x=True, expand_y=True
		],
        
        [sg.Column(song_title_column, background_color='black',
                justification='c', element_justification='c')],
        
        [
            sg.Column([[
            sg.Sizer(0,100),
            
            sg.Image(pad=(10, 0), filename=GO_BACK_IMAGE_PATH, enable_events=True,
                    size=(35, 44), key='previous', background_color='black'),
            sg.Image(filename=PLAY_SONG_IMAGE_PATH,
                    size=(64, 64), pad=(10, 0), enable_events=True, key='play', background_color='black'),
            sg.Image(filename=PAUSE_SONG_IMAGE_PATH,
                    size=(58, 58), pad=(10, 0), enable_events=True, key='pause', background_color='black'),
            sg.Image(filename=GO_FORWARD_IMAGE_PATH, enable_events=True,
                    size=(35, 44), pad=(10, 0), key='next', background_color='black')
            ]], expand_x=True, element_justification="center", background_color="black")
        ],
        [sg.Column(layout=currently_playing, justification='c',
                element_justification='c', background_color='black', pad=None)]


    ]
    window = sg.Window('TravelTales Audio Player', layout=main, size=(
        WINDOW_WIDTH, WINDOW_HEIGHT), background_color='black', finalize=True, grab_anywhere=True, resizable=False,)



    def update_song_display():
        news_player_obj.add_news_to_played(current_news_obj)    #TODO: call this method only if the news is played for more than xx%
        window['news_image'].update(current_news_obj.get_news_image_local_path())
        window["news_summary"].update(textwrap.fill(current_news_obj.get_summary(), 40))
        window['song_name'].update(textwrap.fill(current_news_obj.get_title(), 60))
        window['currently_playing'].update(
            f'Playing: {textwrap.shorten(current_news_obj.get_title(), 100)}')

    #first_time = True
    MusicUtilites.start_music(MUSIC_FOLDER)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            MusicUtilites.stop_sounds()
            break
        elif event == 'play':
            if MusicUtilites.is_sound_playing():
                pass
            if MusicUtilites.is_sound_playing() == False:
                MusicUtilites.play_sound(current_news_obj.get_wav_local_path())
                update_song_display()

        elif event == 'pause':
            if MusicUtilites.is_sound_playing() or MusicUtilites.is_music_playing():
                MusicUtilites.pause_sounds()
            else:
                MusicUtilites.unpause()
            pass

        elif event == 'next':
            next_news = news_player_obj.get_next_news(check_if_already_played=False)
            if next_news == current_news_obj:
                print("! next news is the same as current!")
                pass
            current_news_obj = next_news
            update_song_display()
            MusicUtilites.play_sound(current_news_obj.get_wav_local_path())


        elif event == 'previous':
            prev_news = news_player_obj.get_previous_news()
            if prev_news is None:
                continue
            if prev_news == current_news_obj:
                print("! prev news is the same as current!")
                pass
            current_news_obj = prev_news
            update_song_display()
            MusicUtilites.play_sound(current_news_obj.get_wav_local_path())

        elif event == 'btn_show_plots':
            data_visualization_window(users_manager_obj.get_passengers_objs(), [current_news_obj])
            pass

    window.close()