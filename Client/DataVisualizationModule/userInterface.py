import PySimpleGUI as sg
import os
import textwrap

from NewsPlayingModule.news import News
from user import User

from DataVisualizationModule.radarChart import radar_chart
from DataVisualizationModule.pcaPlot import pca_plot

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use('TkAgg')

#sg.set_options(dpi_awareness=True)
#https://github.com/PySimpleGUI/PySimpleGUI/issues/4713

#https://github.com/PySimpleGUI/PySimpleGUI/issues/5410


WINDOW_WIDTH = 700
WINDOW_HEIGHT = 580

"""
This file handles the window dedicated to the data plotting of given news and users
it has to show in the window:
- one plot for the star plot
- one plot for the PCA representation
"""

def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1) #, expand=1
    return figure_canvas_agg

def data_visualization_window(users_list : list[User], news_list : list[News]):

    
    sg.theme('Reddit')

    embeddings = []

    for user in users_list:
        embeddings.append(user.get_embedding())

    for news in news_list:
        embeddings.append(news.get_embedding())


    main = [
        
        [sg.Column(layout=[[sg.Text('Data Visualization'
                , background_color='black', text_color='white',  font=('Tahoma', 16))]], justification='c',
                element_justification='c', background_color='black')],
        [
            
            #sg.Column([[
                sg.Graph(
                    canvas_size=(350, 350), graph_bottom_left=(0, 0), graph_top_right=(350, 350), pad=None, key="radar_plot"),
                    #]], size=(350, 350)),
            sg.Graph(
                    canvas_size=(350, 350), graph_bottom_left=(0, 0), graph_top_right=(350, 350), pad=None, key="pca_plot"),
            
        ],
        
        [sg.HorizontalSeparator("white")],

    ]
    window = sg.Window('TravelTales Data Visualization', layout=main, size=(
        WINDOW_WIDTH, WINDOW_HEIGHT), background_color='black', finalize=True, grab_anywhere=True, resizable=False,)

    dpi = window.TKroot.winfo_fpixels('1i')
    #print(f"DPI BEFORE is {dpi}")
    fig = radar_chart(embeddings, dpi=dpi)
    fig2 = pca_plot(embeddings)
    #print(f"DPI AFTER is {window.TKroot.winfo_fpixels('1i')}")

    fig_canvas_agg = draw_figure(window['radar_plot'].TKCanvas, fig)
    fig_canvas_agg2 = draw_figure(window['pca_plot'].TKCanvas, fig2)

    #fig_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    #(w,h) = fig_canvas_agg.get_width_height()
    #print(f"[W, H]: {w}, {h}")
    #print(f"get_screen_dimensions: {window.get_screen_dimensions()}")

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break

    window.close()