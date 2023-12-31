import numpy as np
from matplotlib import pyplot as plt

from matplotlib.figure import Figure

target_names = ['business','entertainment','politics','sport','tech']


def radar_chart(values_array, colors, title='Radar Chart', categories=target_names, figsize=(3.5, 3.5), dpi=95):
    # Number of categories
    num_categories = len(categories)

    if colors is not None:
      assert len(values_array) == len(colors), "the given colors array len is != from len(values_array)"

    # Calculate angle for each category
    angles = np.linspace(0, 2 * np.pi, num_categories, endpoint=False).tolist()

    values_copy=[]
    # Make the plot circular
    for i in range(len(values_array)):
      values_copy.append(values_array[i] + values_array[i][:1])
    angles += angles[:1]

    # Plot
    #https://github.com/PySimpleGUI/PySimpleGUI/issues/5410
    #fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(polar=True), dpi=dpi)
    fig = Figure(figsize=figsize) #, dpi=dpi
    ax = fig.add_subplot(polar=True)
    
    for i in range(len(values_array)):
      ax.fill(angles, values_copy[i], color=colors[i], alpha=0.5)
      ax.plot(angles, values_copy[i], color=colors[i], alpha=0.25)

    # Set the y-axis limit to 1
    #TODO: set limits according to a logic that can also show elements with zero and negative values
    ax.set_ylim(bottom=-0.1, top=1)

    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    
    #ax.set_title(title, size=12, color='blue', y=1.1)

    #print(f"values_array: {values_array}")
    #print(f"values_copy: {values_copy}")
    #print(f"angles: {angles}")
    
    return fig
    # Add a title
    #plt.title(title, size=12, color='blue', y=1.1)
#
    ## Show the plot
    #plt.show()