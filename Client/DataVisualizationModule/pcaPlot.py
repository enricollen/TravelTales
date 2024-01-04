import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler

def pca_plot(embeddings_array, colors, n_components=2, title='PCA Plot', figsize=(3.5, 3.5), dpi=95):
    # Assuming you have a numpy array 'embeddings' with shape (num_articles, 5)
    # Replace this with your actual data
    # For example, if you have a list of embeddings, you can convert it to a numpy array like this:
    # embeddings = np.array(list_of_embeddings)
    # Create and fit PCA model
    if colors is not None:
      assert len(embeddings_array) == len(colors), "the given colors array len is != from len(embeddings_array)"

    embeddings_array = np.array(embeddings_array)

    n_components = min(n_components, min(embeddings_array.shape))

    if n_components > 3:
        print(f"[+] PCA maximum n_components is set to 3, {n_components} given")
        n_components = 3
    
    pca = PCA(n_components=n_components)
    embeddings_PCA = pca.fit_transform(embeddings_array)
    
    # Calculate the norm for each row (axis=1)
    norms = np.linalg.norm(embeddings_PCA, axis=1)
    # Divide each PCA component by its norm
    embeddings_PCA = embeddings_PCA / norms[:, np.newaxis]

    # Plot the 2D embeddings
    #plt.figure(figsize=figsize)
    fig = Figure(figsize=figsize) # , dpi=dpi
    ax = fig.add_subplot()

    if n_components < 2:
        print(f"[!] Could not compute PCA for less than 2 components [!]")
        return fig
    
    if n_components == 2:
        ax.scatter(embeddings_PCA[:, 0], embeddings_PCA[:, 1], c=colors, alpha=0.5)
    else:
        ax.scatter(embeddings_PCA[:, 0], embeddings_PCA[:, 1], embeddings_PCA[:, 2], c=colors, alpha=0.5)
    
    # Add labels and title
    ax.set_title(f'{n_components}D PCA of News Article Embeddings')
    #ax.set_xlabel('Principal Component 1')
    #ax.set_ylabel('Principal Component 2')

    # Add labels to each point
    #for i, label in enumerate(labels_array):
    #    plt.annotate(label, (embeddings_2d[i, 0], embeddings_2d[i, 1]))

    # Show the plot
    #plt.show()
    return fig