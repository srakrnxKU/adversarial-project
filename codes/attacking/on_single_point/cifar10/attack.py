import torch
import torch.nn.functional as F
from torch import nn, optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms


def maxloss(model, criterion, dataset, epsilon=1, lr=0.1, n_epoches=10, verbose=False):
    """Generate perturbations on the dataset when given a model and a criterion
    using a maximised loss method

    Parameters
    ----------
    model: nn.module
        A model to attack
    criterion: function
        A criterion function
    optimizer: torch.optim
        An optimizer class object used to optimize the maximised loss
    dataset: torchvision.datasets
        torchvision-like dataset
    epsilon: float
        Maximum value to clamp for the perturbation
    n_epohes: int
        Epoches to maximise the loss
    verbose: bool
        Verbosity setting

    Returns
    -------
    torch.tensor
        A tensor containing perturbations with the same length of the
        received dataset.
    """
    loader = DataLoader(dataset, batch_size=1, shuffle=False)
    perturbs = []
    model.eval()

    for i, (image, label) in enumerate(loader):
        if verbose:
            print("Image:", i + 1)
        #  Create a random array of perturbation
        perturb = torch.zeros(image.shape, requires_grad=True)
        optimizer = optim.Adam([perturb], lr=lr)

        #  Train the adversarial noise, maximising the loss
        for e in range(n_epoches):
            running_loss = 0
            optimizer.zero_grad()

            output = model(image + perturb)
            loss = -criterion(output, label)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
            perturb.data.clamp_(-epsilon, epsilon)
        if verbose:
            print("\tNoise loss:", -1 * loss.item())
        perturbs.append(perturb)

    perturbs = torch.stack(perturbs)
    return perturbs


def fgsm(model, criterion, dataset, epsilon=-1, verbose=False):
    """Generate perturbations on the dataset when given a model and a criterion

    Parameters
    ----------
    model: nn.module
        A model to attack
    criterion: function
        A criterion function
    dataset: torchvision.datasets
        torchvision-like dataset
    epsilon: float
        Maximum value to clamp for the perturbation
    verbose: bool
        Verbosity setting

    Returns
    -------
    torch.tensor
        A tensor containing perturbations with the same length of the
        received dataset.
    """

    loader = DataLoader(dataset, batch_size=1, shuffle=False)
    perturbs = []
    model.eval()

    for i, (image, label) in enumerate(loader):
        if verbose:
            print("Image:", i + 1)

        #  Create a random array of perturbation
        perturb = torch.zeros(image.shape, requires_grad=True)

        #  Epsilon defines the maximum density (-e, e). It should be
        #  in the range of the training set's scaled value.
        epsilon = 1

        adversarial_optimizer = optim.Adam([perturb], lr=0.1)

        image.requires_grad = True

        output = model(image)
        loss = -criterion(output, label)
        loss.backward()

        perturb = image.grad.data.sign()
        perturbs.append(perturb)

    perturbs = torch.stack(perturbs)
    return perturbs