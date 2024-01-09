import os
import threading
import PySimpleGUI as sg
import textwrap

from NewsPlayingModule.utils.music_utilities import MusicUtilites  # play_sound, is_sound_playing, pause_sounds, stop_sounds, unpause

from NewsPlayingModule.news import News
from NewsPlayingModule.newsPlayer import NewsPlayer
from usersManager import UsersManager

from FeedbackEstimationModule.FeedbackEstimator import FeedbackEstimator

from DataVisualizationModule.userInterface import data_visualization_window
from FeedbackEstimationModule.userInterface import FeedbackWindow

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
"""
first_news_shown = False

def player_window(news_player_obj: NewsPlayer, users_manager_obj: UsersManager, feedback_estimator: FeedbackEstimator):
    current_news_obj = news_player_obj.get_current_news()

    global first_news_shown

    DEFAULT_IMAGE_PATH = os.path.join("NewsPlayingModule", "Images", "travel-tales.png")  

    DEFAULT_TITLE_TEXT = 'Press play to read news'

    sg.theme('Reddit')
    news_title_column = [
        [sg.Text(text=DEFAULT_TITLE_TEXT, justification='center', background_color='black',
                 text_color='white', size=(200, 0), font='Tahoma', key='txt_news_title', enable_events=True)]
    ]

    player_info = [
        [sg.Text('TravelTales Player'
                  , background_color='black', text_color='white', font=('Tahoma', 7))]  #
    ]

    currently_playing = [
        [sg.Text(background_color='black', size=(200, 0), text_color='white',
                 font=('Tahoma', 10), key='currently_playing')]
    ]

    GO_BACK_IMAGE_PATH = os.path.join("NewsPlayingModule", "Images", "back.png")  
    GO_FORWARD_IMAGE_PATH = os.path.join("NewsPlayingModule", "Images", "next.png")  
    PLAY_SONG_IMAGE_PATH = os.path.join("NewsPlayingModule", "Images", "play_button.png")  
    PAUSE_SONG_IMAGE_PATH = os.path.join("NewsPlayingModule", "Images", "pause.png")  
    DISABLED_MUSIC_IMAGE_PATH = os.path.join("NewsPlayingModule", "Images", "disable_ambient_music.png")
    ENABLED_MUSIC_IMAGE_PATH = os.path.join("NewsPlayingModule", "Images", "enable_ambient_music.png")

    main = [

        [sg.Column(layout=player_info, justification='c',
                   element_justification='c', background_color='black')],
        [

            sg.Image(filename=DEFAULT_IMAGE_PATH,
                     size=(350, 350), pad=None, key="news_image"),
            sg.Text("News summary", key="news_summary", background_color="black", text_color="white",
                    font=('Tahoma', 10), expand_x=True, justification="center")

        ],
        [sg.Column([
            [sg.Sizer(WINDOW_WIDTH, 0)],
            [
                sg.Button("Show plots", key="btn_show_plots", expand_x=True),
                sg.Sizer(WINDOW_WIDTH / 3, 0),
                sg.Button("Collect Feedback", key="btn_feedback_gathering", expand_x=True)]
            ],
            element_justification="center", background_color="black")  # ,expand_x=True, expand_y=True
        ],

        [sg.Column(news_title_column, background_color='black',
                   justification='c', element_justification='c')],

        [
            sg.Column([[
                sg.Sizer(0, 100),

                sg.Image(pad=(10, 0), filename=GO_BACK_IMAGE_PATH, enable_events=True,
                         size=(35, 44), key='previous', background_color='black'),
                sg.Image(filename=PLAY_SONG_IMAGE_PATH,
                         size=(64, 64), pad=(10, 0), enable_events=True, key='play', background_color='black'),
                sg.Image(filename=PAUSE_SONG_IMAGE_PATH,
                         size=(58, 58), pad=(10, 0), enable_events=True, key='pause', background_color='black'),
                sg.Image(filename=GO_FORWARD_IMAGE_PATH, enable_events=True,
                         size=(35, 44), pad=(10, 0), key='next', background_color='black'),
                sg.Image(filename=DISABLED_MUSIC_IMAGE_PATH, enable_events=True,
                         size=(35, 44), pad=(10, 0), key='disabled-music', background_color='black', visible=True),
                sg.Image(filename=ENABLED_MUSIC_IMAGE_PATH, enable_events=True,
                         size=(35, 44), pad=(10, 0), key='enabled-music', background_color='black', visible=False)
            ]], expand_x=True, element_justification="center", background_color="black")
        ],
        [sg.Column(layout=currently_playing, justification='c',
                   element_justification='c', background_color='black', pad=None)]

    ]
    window = sg.Window('TravelTales Audio Player', layout=main, size=(
        WINDOW_WIDTH, WINDOW_HEIGHT), background_color='black', finalize=True, grab_anywhere=True, resizable=False, )

    feedback_window = None 

    def compute_feedback_thread(feedback_window):
        #feedback_window.capture_prints()
    
        feedback_dict = feedback_estimator.compute_feedback(current_news_obj, feedback_window)
        
        #call the callback function to update the feedback window with feedback faces
        #w.r.t. the user engagement level contained inside the feedback_dict
        feedback_window.display_user_data(feedback_dict)
        
        #feedback_window.update_prints()
        #feedback_window.release_prints()
        if not window.is_closed():
            window['btn_feedback_gathering'].update(disabled=False, text='Collect Feedback')
    
        return feedback_dict

    def update_news_infos_display():
        global first_news_shown
        first_news_shown = True
        news_player_obj.add_news_to_played(
            current_news_obj)  # TODO: call this method only if the news is played for more than xx%
        window['news_image'].update(current_news_obj.get_news_image_local_path(use_category_pic=False))
        #window['news_image'].update(current_news_obj.get_news_category_image())
        window["news_summary"].update(
            textwrap.fill(current_news_obj.get_summary(), 40))
        window['txt_news_title'].update(
            textwrap.fill(current_news_obj.get_title(), 60), font=('Tahoma', 14, 'underline'))
        window['currently_playing'].update(
            f'Playing: {textwrap.shorten(current_news_obj.get_title(), 100)}')

    feedback_mode = False
    MusicUtilites.start_music(MUSIC_FOLDER) #uncomment to play ambient music on startup

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            MusicUtilites.stop_sounds()
            break
        elif event == 'txt_news_title':
            if not first_news_shown:
                continue
            import webbrowser
            webbrowser.open(current_news_obj.get_news_link())
            pass
        elif event == 'play':
            if MusicUtilites.is_news_playing():
                pass
            if MusicUtilites.is_news_playing() == False:
                MusicUtilites.play_news(current_news_obj.get_wav_local_path())
                update_news_infos_display()
            if MusicUtilites.is_music_playing():
                MusicUtilites.pause_music()

        elif event == 'pause':
            if MusicUtilites.is_news_playing():
                MusicUtilites.pause_news()
                #MusicUtilites.unpause_music()
                #window['disabled-music'].update(visible = True)
                #window['enabled-music'].update(visible = False)

        elif event == 'next':
            next_news = news_player_obj.get_next_news(
                check_if_already_played=False)
            if next_news == current_news_obj:
                print("! next news is the same as current!")
                pass
            current_news_obj = next_news
            update_news_infos_display()
            MusicUtilites.play_news(current_news_obj.get_wav_local_path())

        elif event == 'previous':
            prev_news = news_player_obj.get_previous_news()
            if prev_news is None:
                continue
            if prev_news == current_news_obj:
                print("! prev news is the same as current!")
                pass
            current_news_obj = prev_news
            update_news_infos_display()
            MusicUtilites.play_news(current_news_obj.get_wav_local_path())
        
        elif event == 'disabled-music':
            window['disabled-music'].update(visible = False)
            window['enabled-music'].update(visible = True)
            MusicUtilites.pause_music()
            
        elif event == 'enabled-music':
            window['enabled-music'].update(visible = False)
            window['disabled-music'].update(visible = True)
            MusicUtilites.unpause_music()

        elif event == 'btn_show_plots':
            data_visualization_window(
                users_manager_obj.get_passengers_objs(), [current_news_obj])

        elif event == 'btn_feedback_gathering':
            if MusicUtilites.music_playing == True:
                MusicUtilites.pause_music()
            
            feedback_mode = not feedback_mode

            if feedback_mode:
                window['btn_feedback_gathering'].update(disabled=True, text='Collecting Feedback...')
                feedback_window = FeedbackWindow()

                feedback_thread = threading.Thread(
                    target=compute_feedback_thread, args=[feedback_window])
                
                feedback_thread.start()
            else:
                if feedback_window and type(feedback_window) == FeedbackWindow:
                    feedback_window.close()
                if feedback_thread and feedback_thread.is_alive():
                    feedback_estimator.stop_gathering()
                    feedback_thread.join(10)
                    print(f"Feedback thread was terminated correctly? {'no' if feedback_thread.is_alive() else 'yes'}")
                window['btn_feedback_gathering'].update(disabled=False, text='Collect Feedback')
        
        if feedback_window is not None and type(feedback_window) == FeedbackWindow:
            event_feedback, values_feedback = feedback_window.window.read()

            if event_feedback == sg.WIN_CLOSED:
                feedback_window.close()
                if feedback_thread and feedback_thread.is_alive():
                    feedback_estimator.stop_gathering()
                    feedback_thread.join(10)
                    print(f"Feedback thread was terminated correctly? {'no' if feedback_thread.is_alive() else 'yes'}")
                window['btn_feedback_gathering'].update(disabled=False, text='Collect Feedback')
            
            elif event_feedback == 'btn_stop_gathering':
                feedback_window.disable_stop_button()
                feedback_estimator.stop_gathering()
                
                pass
                

    window.close()