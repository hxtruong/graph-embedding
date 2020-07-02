import tensorflow as tf
import networkx as nx
import numpy as np
import scipy.sparse as sparse

from data_preprocessing.data_preprocessing import next_datasets, get_graph_from_file
from utils.autoencoder import Autoencoder
from utils.visualize import plot_losses, plot_embedding


class StaticGE(object):
    def __init__(self, G, embedding_dim, hidden_dims, alpha=0.01, beta=2, nu1=0.001, nu2=0.001):
        super(StaticGE, self).__init__()
        self.G = nx.Graph(G)
        self.embedding_dim = embedding_dim
        self.hidden_dims = hidden_dims
        self.alpha = alpha
        self.beta = beta

        self.input_dim = self.G.number_of_nodes()

        self.model = Autoencoder(
            input_dim=self.input_dim,
            embedding_dim=self.embedding_dim,
            hidden_dims=self.hidden_dims,
            v1=nu1,
            v2=nu2
        )
        self.A, self.L = self.create_A_L_matrix()

    def compute_loss(self, model, inputs, alpha=0.01, beta=2):
        '''

        :param model:
        :param inputs:
        :param alpha:
        :param beta:
        :return:
        '''

        def loss_1st(Y, L):
            # 2 * tr(Y^T * L * Y)
            return 2 * tf.linalg.trace(
                tf.linalg.matmul(tf.linalg.matmul(tf.transpose(Y), L), Y)
            )

        def loss_2nd(X_hat, X, beta):
            B = np.ones_like(X)
            B[X != 0] = beta
            return tf.reduce_sum(tf.pow((X_hat - X) * B, 2))

        X, L = inputs
        X_hat, Y = model(X)

        # batch_size = X.shape[0]
        # TODO: check if divide batch_size

        loss_1 = loss_1st(Y, L)
        loss_2 = loss_2nd(X_hat, X, beta)
        return loss_2 + alpha * loss_1

    def train(self, batch_size=1, epochs=10, learning_rate=0.003):
        def train_func(loss, model, opt, inputs, alpha, beta):
            with tf.GradientTape() as tape:
                gradients = tape.gradient(
                    loss(model, inputs, alpha, beta),
                    model.trainable_variables
                )
            gradient_variables = zip(gradients, model.trainable_variables)
            opt.apply_gradients(gradient_variables)

        # ---------
        writer = tf.summary.create_file_writer('tmp')

        graph_embedding_list = []
        losses = []

        # datasets = get_transform(self.tf_dataset, batch_size=1, prefetch_times=1, shuffle=False)
        tf.keras.backend.clear_session()
        opt = tf.optimizers.Adam(learning_rate=learning_rate)
        with writer.as_default():
            with tf.summary.record_if(True):
                for epoch in range(epochs):
                    epoch_loss = []
                    for step, batch_inp in next_datasets(self.A, self.L, batch_size=batch_size):
                        train_func(self.compute_loss, self.model, opt, batch_inp, alpha=self.alpha,
                                   beta=self.beta)
                        loss_values = self.compute_loss(self.model, batch_inp, alpha=self.alpha,
                                                        beta=self.beta)
                        epoch_loss.append(loss_values)
                    # tf.summary.scalar('loss', loss_values, step=epoch)
                    # embedding = self.get_embedding()
                    mean_epoch_loss = np.mean(epoch_loss)
                    if epoch % 5 == 0:
                        print(f"\tEpoch {epoch}: Loss = {mean_epoch_loss}")
                    losses.append(mean_epoch_loss)

                    # if epoch % 50 == 0:
                    #     plot_embedding(embedding[:max(500, embedding.shape[0]), :])

                plot_losses(losses, title="Train GE", x_label="Epoch", y_label="Loss value")
                print(f"Loss = {losses[-1]}")

    def create_A_L_matrix(self):
        A = nx.to_scipy_sparse_matrix(self.G, format='csr').astype(np.float32)
        D = sparse.diags(A.sum(axis=1).flatten().tolist()[0]).astype(np.float32)
        L = D - A
        return A, L

    def get_embedding(self, inputs=None):
        if inputs is None:
            inputs = nx.adj_matrix(self.G).todense()

        return self.model.get_embedding(inputs)


if __name__ == "__main__":
    G_tmp = get_graph_from_file(filename="../data/ca-AstroPh.txt")
    S = nx.adj_matrix(G_tmp).todense()[:1000, :1000]
    # S = np.array([
    #     [0, 2, 0, 4, 5],
    #     [2, 0, 1, 0, 6],
    #     [0, 1, 0, 0, 0],
    #     [4, 0, 0, 0, 0],
    #     [5, 6, 0, 0, 0]
    # ])
    G = nx.from_numpy_matrix(S, create_using=nx.Graph)
    ge = StaticGE(G=G, embedding_dim=64, hidden_dims=[128, 256, 512])
    ge.train(batch_size=64, epochs=1)
    embeddings = ge.get_embedding()
    # evaluate_classify_embeddings(embeddings, label_file=None)
