import numpy as np
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
import warnings

warnings.filterwarnings("ignore")


def read_node_label(filename, skip_head=False):
    X = []
    Y = []
    with open(filename) as fi:
        if skip_head:
            fi.readline()
        for line in fi:
            x, y = line.strip().split()
            X.append(int(x))
            Y.append(y)
    return X, Y


def plot_embeddings(graph, embeddings, path_file=None):
    emb_list = []

    X = []
    Y = []
    if path_file:
        X, Y = read_node_label(path_file)
    else:  # assume all nodes have a default label
        for node in list(graph.nodes()):
            X.append(str(node))
            Y.append("0")

    for k in X:
        emb_list.append(embeddings[k])

    emb_list = np.array(emb_list)

    model = TSNE(n_components=2)
    node_pos = model.fit_transform(emb_list)

    color_idx = {}
    for i in range(len(X)):
        color_idx.setdefault(Y[i], [])
        color_idx[Y[i]].append(i)

    for c, idx in color_idx.items():
        plt.scatter(node_pos[idx, 0], node_pos[idx, 1], label=c)
    plt.legend()
    plt.show()


def plot_losses(losses, title=None, x_label=None, y_label=None):
    fig = plt.figure()
    plt.plot(losses)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)

    plt.show()


def plot_embedding(embedding):
    X_embedded = TSNE(n_components=2).fit_transform(embedding)
    plt.scatter(X_embedded[:, 0], X_embedded[:, 1])
    plt.show()

# plot_embeded([0])
