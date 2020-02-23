# %%
import logging
import os
import sys

import torch
from torch import nn, optim

from clustre.attacking.on_single_point.attack import pgd  # isort:skip
from clustre.helpers.mnist_helpers import mnist_fcnn_model, testloader  # isort:skip

logging.basicConfig(
    filename=f"logs/{os.path.basename(__file__)}.log",
    filemode="a",
    level="INFO",
    format="%(process)d-%(levelname)s-%(asctime)s-%(message)s",
)
# %%
OUTPUT_PATH = "perturbs/on_single_point/mnist/fcnn_pgd_perturbs_testset.pt"

# %%
criterion = nn.CrossEntropyLoss()
logging.info("Started running")
perturbs = pgd(mnist_fcnn_model, criterion, testloader, verbose=True, cuda=True)
logging.info("Ended running")
#  %%
torch.save(perturbs, OUTPUT_PATH)