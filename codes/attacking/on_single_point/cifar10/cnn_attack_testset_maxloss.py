# %%
import os

import torch
from torch import nn, optim

from attack import maxloss
from cifar10_helpers import cifar10_cnn_model, cifar10_testset

# %%
OUTPUT_PATH = "perturbs/on_single_point/cifar10/cnn_maxloss_perturbs_testset.pt"

# %%
criterion = nn.CrossEntropyLoss()
perturbs = maxloss(cifar10_cnn_model, criterion, cifar10_testset, verbose=True)
#  %%
torch.save(perturbs, OUTPUT_PATH)
