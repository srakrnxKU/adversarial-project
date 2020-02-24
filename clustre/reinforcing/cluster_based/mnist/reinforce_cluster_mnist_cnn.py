# %%
import argparse
import logging
import os
import sys

import torch
import torch.nn.functional as F
from torch import nn, optim
from torch.utils.data import DataLoader, Dataset
from torchvision import datasets, transforms

from clustre.helpers import mnist_helpers
from clustre.reinforcing import helpers as reinforce_helpers
from clustre.reinforcing.cluster_based import reinforce

parser = argparse.ArgumentParser()
parser = argparse.ArgumentParser(description='Reinforce using cluster-based method')
parser.add_argument('--eps', type=float, default=0.2, help='Epsilon')
parser.add_argument('--nclus', type=int, default=100, help='Amount of clusters')
parser.add_argument('--clus', type=str, default="fgsm", help='Output dir for image')
parser.add_argument('--learn', type=str, default="pgd", help='Output dir for image')

# PARAMETERS
args = parser.parse_args()

EPSILON = args.eps
N_CLUSTERS = args.nclus
CLUSTERING_PERTURB = args.clus
LEARNING_PERTURB = args.learn

logging.basicConfig(
    filename=f"logs/{os.path.basename(__file__)}.log",
    filemode="a",
    level="INFO",
    format="%(process)d-%(levelname)s-%(asctime)s-%(message)s",
)

# %%
model = mnist_helpers.mnist_cnn_model

# %%
trainset_fgsm_perturbs = torch.load(
    "perturbs/on_single_point/mnist/fcnn_fgsm_perturbs_trainset.pt"
)
testset_fgsm_perturbs = torch.load(
    "perturbs/on_single_point/mnist/fcnn_fgsm_perturbs_testset.pt"
)
trainset_pgd_perturbs = torch.load(
    "perturbs/on_single_point/mnist/fcnn_pgd_perturbs_trainset.pt"
)
testset_pgd_perturbs = torch.load(
    "perturbs/on_single_point/mnist/fcnn_pgd_perturbs_testset.pt"
)

# %%
logging.info(f"EPSILON = {EPSILON}")
logging.info(f"N_CLUSTERS = {N_CLUSTERS}")
logging.info(f"CLUSTERING_PERTURB = {CLUSTERING_PERTURB}")
logging.info(f"LEARNING_PERTURB = {LEARNING_PERTURB}")

if CLUSTERING_PERTURB == "pgd":
    clustering_perturbs = trainset_pgd_perturbs
elif CLUSTERING_PERTURB == "fgsm":
    clustering_perturbs = trainset_fgsm_perturbs

# %%
reinforce_helpers.accuracy_unattacked(model, mnist_helpers.testloader, desc="Accuracy")
reinforce_helpers.accuracy_attacked(
    model, mnist_helpers.testloader, testset_pgd_perturbs, desc="PGD accuracy"
)
reinforce_helpers.accuracy_attacked(
    model, mnist_helpers.testloader, testset_fgsm_perturbs, desc="FGSM accuracy"
)

# %%
train_target, train_perturb, train_km = reinforce.calculate_k_perturbs(
    model,
    mnist_helpers.mnist_trainset,
    clustering_perturbs.detach().cpu().numpy(),
    N_CLUSTERS,
    verbose=True,
    cuda=True,
    attack_method=LEARNING_PERTURB
)

ad = reinforce.AdversarialDataset(
    mnist_helpers.mnist_trainset, train_target, train_perturb, cuda=False
)
adversarialloader = DataLoader(ad, batch_size=16, shuffle=True)

trainloader = DataLoader(mnist_helpers.mnist_trainset, batch_size=32, shuffle=False)
logging.info(f"Started reinforcing on {reinforce.get_time()}")
reinforced_model = reinforce.k_reinforce(model, trainloader, adversarialloader, cuda=True)
logging.info(f"Finished reinforcing on {reinforce.get_time()}")

# %%
reinforce_helpers.accuracy_unattacked(reinforced_model, mnist_helpers.testloader, desc="Accuracy")
reinforce_helpers.accuracy_attacked(
    reinforced_model, mnist_helpers.testloader, testset_pgd_perturbs, desc="PGD accuracy"
)
reinforce_helpers.accuracy_attacked(
    reinforced_model, mnist_helpers.testloader, testset_fgsm_perturbs, desc="FGSM accuracy"
)
