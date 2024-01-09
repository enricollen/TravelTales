import os
import PySimpleGUI as sg
from io import StringIO
import sys

DEFAULT_IMAGE_PATH = os.path.join("NewsPlayingModule", "Images", "travel-tales.png")

USE_VIDEO = True if os.getenv("USE_VIDEO").lower() in ["true", "yes", "1"] else False
WEBCAM_IMAGE_SIZE = (400, 300)

WINDOW_WIDTH = 850
WINDOW_HEIGHT = 500

class FeedbackWindow:
    def __init__(self):
        sg.theme('Reddit')

        # buffer to redirect prints
        #self.print_output = StringIO()
        #sys.stdout = self.print_output

        output_column = [
            [sg.Text('Feedback Output:', text_color='white', background_color='black')],
            [sg.Multiline(size=(60, 20), text_color='white', background_color='black', key='feedback_output')],
        ]

        image_column = [
            [sg.Image(filename='', key=f'image_{i}', size=(30, 30), background_color='black') for i in range(3)],
            [sg.Text('', key=f'username_{i}', text_color='white', background_color='black') for i in range(3)]
        ]

        table_column = [
            [sg.Table(values=[], headings=['Username', 'Duration', 'Audio Sentiment', 'Engagement'] + (['Video sentiment', 'Video engagement', 'Mixed engagement'] if USE_VIDEO else []), justification='center', key='user_table', max_col_width=20, def_col_width = 10, col_widths=10, hide_vertical_scroll=True, vertical_scroll_only=False, auto_size_columns=False)],
        ]

        first_row = [sg.Column(output_column, background_color='black')]

        if USE_VIDEO:
            webcam_row = [
                [sg.Image(filename=DEFAULT_IMAGE_PATH,
                        size=WEBCAM_IMAGE_SIZE, pad=None, key="webcam_image")]
            ]
        
        first_row.append(sg.Column( 
            (webcam_row if USE_VIDEO else []) + [[sg.Button("Stop gathering", key="btn_stop_gathering")]],
              background_color='black', element_justification="center"))

        layout = [
            first_row,
            [sg.Column(table_column, background_color='black'), sg.Column(image_column, background_color='black')]
        ]

        self.window = sg.Window('Feedback Collection', layout, size=(WINDOW_WIDTH, WINDOW_HEIGHT), background_color='black', resizable=True, finalize=True)

    #def capture_prints(self):
    #    sys.stdout = self.print_output
        
    #def release_prints(self):
    #    sys.stdout = sys.__stdout__

    def print(self, string):
        if self.is_closed():
            return
        self.window['feedback_output'].update(value=string)
    #def update_prints(self):
    #    self.window['feedback_output'].update(value=self.print_output.getvalue())

    def show_image(self, image_buffer):
        if USE_VIDEO is False:
            return
        if self.is_closed():
            return
        self.window['webcam_image'].update(image_buffer)
        pass

    #def update_single_line_output(self, line_length):
    #    print_output_length = len(self.print_output.getvalue())
    #    self.print_output.seek(print_output_length - line_length)
    #    self.window['feedback_output'].update(value=self.print_output.getvalue())
    closed = False

    def disable_stop_button(self):
        if self.is_closed():
            return
        self.window['btn_stop_gathering'].update(disabled=True)

    def is_closed(self):
        return self.window.is_closed() or self.closed

    def close(self):
        self.closed = True
        self.window.close()

    def display_user_data(self, feedback_data):
        if self.is_closed():
            return
        
        for i in range(3):
            self.window[f'image_{i}'].Update(filename='')
            self.window[f'username_{i}'].Update(value='')

        # get user feedback data from dictionary
        user_feedback = feedback_data.get('users-feeback', [])

        high_interest = os.path.join(os.path.dirname(__file__), "Images", "high.png")
        medium_interest = os.path.join(os.path.dirname(__file__), "Images", "medium.png")
        low_interest = os.path.join(os.path.dirname(__file__), "Images", "low.png")
        lowest_interest = os.path.join(os.path.dirname(__file__), "Images", "lowest.png")

        data = []
        for i, user in enumerate(user_feedback):
            username = user.get('username', '')
            engagement_score = user.get('engagement_score', 0)
            predicted_sentiment = user.get('predicted_sentiment', 'neutral')
            audio_duration = user.get('audio_duration', 0)

            if USE_VIDEO:
                visual_emotion = user.get('visual_emotion', 'NA')
                visual_engagement_score = user.get('engagement_score_video', -1)
                mixed_engagement_score = user.get('engagement_score_mixed', -1)

            if 0 <= engagement_score < 2.5:
                image_filename = lowest_interest
            elif 2.5 <= engagement_score < 5:
                image_filename = low_interest
            elif 5 <= engagement_score < 7.5:
                image_filename = medium_interest
            else:
                image_filename = high_interest

            # update the image and username on the GUI
            self.window[f'image_{i}'].Update(filename=image_filename)
            self.window[f'username_{i}'].Update(value=username)

            # update data inside the table
            data.append([username, audio_duration, predicted_sentiment, engagement_score] + ([visual_emotion, visual_engagement_score, mixed_engagement_score] if USE_VIDEO else []))

        self.window['user_table'].update(values=data)