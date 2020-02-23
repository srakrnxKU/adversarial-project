import torch
import torch.nn.functional as F
from torch import nn, optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms


def pgd(
    model, criterion, loader, epsilon=0.3, n_epoches=40, verbose=False, cuda=False,
):
    """Generate perturbations on the dataset when given a model and a criterion
    using a maximised loss method

    Parameters
    ----------
    model: nn.module
        A model to attack
    criterion: function
        A criterion function
    loader: DataLoader
        A DataLoader instance with batch_size=1
    epsilon: float
        Maximum value to clamp for the perturbation
    lr: float
        Learning rate for the perturbation optimizer
    n_epohes: int
        Epoches to maximise the loss
    verbose: bool
        Verbosity setting
    cuda: bool
        If set to `True`, will use CUDA.

    Returns
    -------
    torch.tensor
        A tensor containing perturbations with the same length of the
        received dataset.
    """
    perturbs = []

    for i, (image, label) in enumerate(loader):
        if verbose:
            print("Image:", i + 1)

        perturb = pgd_single_point(
            model,
            criterion,
            image,
            label,
            epsilon=epsilon,
            n_epoches=n_epoches,
            verbose=verbose,
            cuda=cuda,
        )
        perturbs.append(perturb)

    perturbs = torch.stack(perturbs)
    return perturbs.cpu()


def pgd_array(
    model,
    criterion,
    images,
    labels,
    epsilon=0.3,
    n_epoches=40,
    verbose=False,
    cuda=False,
):
    """Generate perturbations on the dataset when given a model and a criterion
    using a maximised loss method

    Parameters
    ----------
    model: nn.module
        A model to attack
    criterion: function
        A criterion function
    images: torch.Tensor
        Images to attack
    labels: torch.Tensor
        Labels for the images
    epsilon: float
        Maximum value to clamp for the perturbation
    lr: float
        Learning rate for the perturbation optimizer
    n_epohes: int
        Epoches to maximise the loss
    verbose: bool
        Verbosity setting
    cuda: bool
        If set to `True`, will use CUDA.

    Returns
    -------
    torch.tensor
        A tensor containing perturbations with the same length of the
        received dataset.
    """
    perturbs = []

    for i, (image, label) in zip(images, labels):
        if verbose:
            print("Image:", i + 1)

        image.unsqueeze_(0)
        label = torch.tensor([label])

        perturb = pgd_single_point(
            model,
            criterion,
            image,
            label,
            epsilon=epsilon,
            n_epoches=n_epoches,
            verbose=verbose,
            cuda=cuda,
        )
        perturbs.append(perturb)

    perturbs = torch.stack(perturbs)
    return perturbs.cpu()


def pgd_single_point(
    model,
    criterion,
    images,
    labels,
    epsilon=0.3,
    step_size=2 / 255,
    n_epoches=40,
    verbose=False,
    cuda=False,
):
    """Generate a perturbation attacking a group of images and labels

    Parameters
    ----------
    model: nn.module
        A model to attack
    criterion: function
        A criterion function
    images: torch.Tensor
        Images to attack
    labels: torch.Tensor
        Labels for the images
    epsilon: float
        Maximum value to clamp for the perturbation
    n_epohes: int
        Epoches to maximise the loss
    verbose: bool
        Verbosity setting
    cuda: bool
        If set to `True`, will use CUDA.

    Returns
    -------
    torch.tensor
        A tensor containing perturbations, with the shape of `images.shape[1:]`
    """
    model.eval()

    if cuda:
        model.to("cuda")
        images = images.to("cuda")
        labels = labels.to("cuda")
    else:
        model.to("cpu")
        images = images.to("cpu")
        labels = labels.to("cpu")

    original_image = images.clone().detach()

    for e in range(n_epoches):
        images.requires_grad = True

        output = model(images)

        model.zero_grad()
        loss = criterion(output, labels)
        loss.backward()

        adversarial_images = images + step_size * images.grad.mean(
            dim=0
        ).sign().unsqueeze_(0)
        perturb = torch.clamp(
            adversarial_images - original_image, min=-epsilon, max=epsilon
        )
        images = torch.clamp(original_image + perturb, min=-1, max=1).detach()
    return (images - original_image).cpu() / epsilon


def fgsm(model, criterion, loader, epsilon=0.3, verbose=False, cuda=False):
    """Generate perturbations on the dataset when given a model and a criterion

    Parameters
    ----------
    model: nn.module
        A model to attack
    criterion: function
        A criterion function
    loader: DataLoader
        A DataLoader instance with batch_size=1
    epsilon: float
        Maximum perturbation density
    verbose: bool
        Verbosity setting
    cuda: bool
        If set to `True`, will use CUDA.

    Returns
    -------
    torch.tensor
        A tensor containing perturbations with the same length of the
        received dataset.
    """
    perturbs = []
    model.eval()

    if cuda:
        model.to("cuda")
    else:
        model.to("cpu")

    for i, (image, label) in enumerate(loader):
        if verbose:
            print(f"Image {i+1}")

        perturb = fgsm_single_point(model, criterion, image, label, epsilon=epsilon, cuda=cuda)
        perturbs.append(perturb)

    perturbs = torch.stack(perturbs)
    return perturbs.cpu()


def fgsm_array(model, criterion, images, labels, epsilon=0.3, verbose=False, cuda=False):
    """Generate perturbations on the dataset when given a model and a criterion

    Parameters
    ----------
    model: nn.module
        A model to attack
    criterion: function
        A criterion function
    images: torch.Tensor
        Images to attack
    labels: torch.Tensor
        Labels for the images
    epsilon: float
        Maximum perturbation density
    verbose: bool
        Verbosity setting
    cuda: bool
        If set to `True`, will use CUDA.

    Returns
    -------
    torch.tensor
        A tensor containing perturbations with the same length of the
        received dataset.
    """
    perturbs = []

    for i, (image, label) in enumerate(zip(images, labels)):
        if verbose:
            print(f"Image {i+1}")

        image.unsqueeze_(0)
        label = torch.tensor([label])

        perturb = fgsm_single_point(model, criterion, image, label, epsilon=epsilon, cuda=cuda)
        perturbs.append(perturb)

    perturbs = torch.stack(perturbs)
    return perturbs.cpu()


def fgsm_single_point(model, criterion, images, labels, epsilon=0.3, cuda=False):
    """Generate a perturbation attacking a group of images and labels

    Parameters
    ----------
    model: nn.module
        A model to attack
    criterion: function
        A criterion function
    images: torch.Tensor
        Images to attack
    labels: torch.Tensor
        Labels for the images
    epsilon: float
        Maximum perturbation density
    verbose: bool
        Verbosity setting
    cuda: bool
        If set to `True`, will use CUDA.

    Returns
    -------
    torch.tensor
        A tensor containing perturbations, with the shape of `images.shape[1:]`
    """
    model.eval()

    if cuda:
        model.to("cuda")
        images = images.to("cuda")
        labels = labels.to("cuda")

    images.requires_grad = True

    output = model(images)
    loss = criterion(output, labels)
    loss.backward()

    perturb = images.grad.data.mean(dim=0).sign().unsqueeze_(0) * epsilon
    attack_image = torch.clamp(images + perturb, min=-1, max=1)
    return (attack_image - images)[0].cpu() / epsilon
