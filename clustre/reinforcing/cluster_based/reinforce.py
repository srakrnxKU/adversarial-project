# %%
import logging
import os
import time

import numpy as np
import torch
import torch.nn.functional as F
from sklearn.cluster import KMeans
from sklearn.metrics import classification_report
from torch import nn, optim
from torch.utils.data import DataLoader, Dataset

from clustre.attacking.on_single_point import attack
from clustre.helpers.helpers import get_time

log = logging.getLogger(__name__)

# %%
def calculate_k_perturbs(
    model,
    training_set,
    clusterer,
    k,
    criterion=nn.CrossEntropyLoss(),
    attack_method="fgsm",
    lr=0.1,
    n_epoches=10,
    verbose=0,
):
    """Clustering analysis on the perturbation and attempt to attack the clustered group together.

    Parameters
    ----------
    model: nn.module
        A model to attack
    training_set: torchvision.dataset
        A dataset-like object to be attacked against
    clusterer: numpy.ndarray
        ndarray-like object with the same length as training_set to be clustered on
    k: int
        Amount of clusters
    criterion: function
        A criterion function
    attack_method: "fgsm" or "maxloss"
        A method used to calculate perturbations
    lr: float
        Learning rate for the perturbation optimizer, to be used by the "maxloss" algorithm
    n_epoches: int
        If attack_method is "maxloss", determine the epoches used to maximise the loss
    verbose: int
        Level of verbosity
    log: bool
        Enable logging

    Returns
    -------
    (k_points, k_perturbs, km)
    """
    # Set model to evaluation mode, thus not calculating its gradient
    model.eval()

    # Load the dataset and begin the clustering process
    # Observe that we load the full dataset by defining `batch_size`
    # as the training set's length.
    loader = DataLoader(training_set, batch_size=len(training_set), shuffle=False)
    X, y = next(iter(loader))
    log.info(f"Starting of k-Means at: {get_time()}")
    km = KMeans(n_clusters=k, verbose=verbose, n_init=1)
    km_clusters = km.fit_predict(clusterer.reshape(len(clusterer), -1))
    log.info(f"Ending of k-Means and starting of training at: {get_time()}")

    # Create empty arrays to store results
    k_points = []
    k_perturbs = []

    # Iterate over clusters in k-Means result
    for i in set(km_clusters):
        # Find indices of the data containing only data points in such cluster
        idx = np.where(km_clusters == i)[0]
        # Obtain all data points in the cluster
        data = [training_set[j] for j in idx]
        # Create a trainloader object
        kloader = DataLoader(data, batch_size=len(data), shuffle=False)
        Xk, yk = next(iter(kloader))

        # Print the attacking detail if verbosity is set to true
        if verbose:
            print(f"Training #{i+1} perturb")
            print(f"\tThis set of perturbation will attack {len(data)} data points.")

        if attack_method == "maxloss":
            perturbs = attack.maxloss_single_point(model, criterion, Xk, yk)
        elif attack_method == "fgsm":
            perturbs = attack.fgsm_single_point(model, criterion, Xk, yk)
        k_points.append(idx)
        k_perturbs.append(perturbs.detach())
    log.info(f"Completion of calculation: {get_time()}")
    k_perturbs = torch.stack(k_perturbs)
    return [k_points, k_perturbs, km]


# %%
def get_nth_perturb(n, targets, perturbs):
    """ Return the perturbation according to its index

    Parameters
    ----------
    n: int
        The index of the data point respective to its dataset.
    targets:
        The nested list containing the index of the perturbations
    perturbations:
        The list of perturbations

    Returns
    -------
    torch.tensor
    """
    for i, j in zip(targets, perturbs):
        if i in targets:
            return j
    return None


# %%
class AdversarialDataset(Dataset):
    """
    Adversarial dataset to be feeded to the model
    """

    def __init__(self, data, targets, perturbs, density=0.2):
        """Initialize function for the dataset

        Parameters
        ----------
        data: torch.tensor
            Original unattacked dataset
        targets: torch.tensor
            Target for the original data
        perturbs: torch.tensor
            The perturbation for the dataset
        density: float
            The density of the perturbation, considered as a multiplier
        """
        super().__init__()
        self.data = data
        self.targets = targets
        self.perturbs = perturbs
        self.density = density

    def __len__(self):
        return len(self.data)

    def _get_nth_perturb(self, n):
        for i, j in zip(self.targets, self.perturbs):
            if i in self.targets:
                return j
        return None

    def __getitem__(self, idx):
        X, y = self.data[idx]
        perturb = self._get_nth_perturb(idx)
        return (X + self.density * perturb), y

    # %%


def k_reinforce(
    model,
    trainloader,
    adversarialloader,
    n_epoches=10,
    train_weight=1,
    adversarial_weight=2,
    criterion=nn.CrossEntropyLoss,
    optimizer=optim.Adam,
    drop_last=False,
    cuda=False
):
    """Reinforce the model using cluster-based method

    Parameters
    ----------
    model: nn.module
        Module to reinforce
    trainloader: DataLoader
        Dataloader for training points
    adversarialloader: DataLoader
        Dataloader for adversarial points
    n_epoches: int
        Epoches to retrain
    train_weight: int/float
        Weight to penalise loss on training points
    adversarial_weight: int/float
        Weight to penalise loss on adversarial points
    criterion: function
        Criterion fuction
    optimizer: nn.optim
        Optimizer function
    drop_last: bool
        If set to `True`, will drop the last batch of training point
    cuda: bool
        If set to `True`, will use CUDA
    """
    if cuda:
        model = model.to("cuda")
    log.info(f"Training started: {get_time()}")
    criterion = criterion(reduction="none")
    optimizer = optimizer(model.parameters())
    for e in range(n_epoches):
        running_loss = 0
        for i, ((images, labels), (adver_images, adver_labels)) in enumerate(zip(
            trainloader, adversarialloader
        )):
            print(f"Epoch {e+1} Minibatch {i+1}")
            X = torch.cat([images, adver_images], 0)
            y = torch.cat([labels, adver_labels], 0)
            w = torch.tensor(
                [
                    train_weight if i < len(labels) else adversarial_weight
                    for i in range(len(labels) + len(adver_labels))
                ]
            ).float()
            if (
                not drop_last
                or len(w) == trainloader.batch_size + adversarialloader.batch_size
            ):
                if cuda:
                    X = X.to("cuda")
                    y = y.to("cuda")
                    w = w.to("cuda")
                optimizer.zero_grad()

                output = F.log_softmax(model(X), dim=1)
                loss = torch.dot(criterion(output, y), w)
                loss.backward()
                optimizer.step()

                running_loss += loss.item()
        else:
            print(f"\tTraining loss: {running_loss/len(trainloader)}")
    log.info(f"Training ended: {get_time()}")
    if cuda:
        model = model.to("cpu")
    return model
