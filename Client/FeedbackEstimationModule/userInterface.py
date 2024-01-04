import os
import PySimpleGUI as sg
from io import StringIO
import sys

class FeedbackWindow:
    def __init__(self):
        sg.theme('Reddit')

        # buffer to redirect prints
        self.print_output = StringIO()
        sys.stdout = self.print_output

        output_column = [
            [sg.Text('Feedback Output:', text_color='white', background_color='black')],
            [sg.Multiline(size=(60, 20), text_color='white', background_color='black', key='feedback_output')],
        ]

        image_column = [
            [sg.Image(filename='', key=f'image_{i}', size=(30, 30), background_color='black') for i in range(3)],
            [sg.Text('', key=f'username_{i}', text_color='white', background_color='black') for i in range(3)]
        ]

        layout = [
            [sg.Column(output_column, background_color='black')],
            [sg.Column(image_column, background_color='black')],
        ]

        self.window = sg.Window('Feedback Collection', layout, size=(700, 500), background_color='black', finalize=True)

    def capture_prints(self):
        sys.stdout = self.print_output

    def release_prints(self):
        sys.stdout = sys.__stdout__

    def update_prints(self):
        self.window['feedback_output'].update(value=self.print_output.getvalue())

    def update_single_line_output(self, line_length):
        print_output_length = len(self.print_output.getvalue())
        self.print_output.seek(print_output_length - line_length)
        self.window['feedback_output'].update(value=self.print_output.getvalue())

    def close(self):
        self.window.close()

    def display_user_images(self, feedback_data):
        
        for i in range(3):  
            self.window[f'image_{i}'].Update(filename='')
            self.window[f'username_{i}'].Update(value='')

        # get user feedback data from dictionary
        user_feedback = feedback_data.get('users-feeback', [])

        smiley_face = os.path.join(os.path.dirname(__file__), "Images", "happy.png")
        neutral_face = os.path.join(os.path.dirname(__file__), "Images", "neutral.png")
        sad_face = os.path.join(os.path.dirname(__file__), "Images", "sad.png")

        for i, user in enumerate(user_feedback):
            username = user.get('username', '')
            engagement_score = user.get('engagement_score', 0)

            if 5 < engagement_score:
                image_filename = smiley_face
            elif 3 <= engagement_score <= 5:
                image_filename = neutral_face
            else:
                image_filename = sad_face

            # update the image and username on the GUI
            self.window[f'image_{i}'].Update(filename=image_filename)
            self.window[f'username_{i}'].Update(value=username)
