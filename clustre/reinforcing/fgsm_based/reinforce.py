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


def fgsm_reinforce(
    model,
    trainloader,
    n_epoches=10,
    criterion=nn.CrossEntropyLoss,
    optimizer=optim.Adam,
):
    log.info(f"Training started: {get_time()}")
    criterion = criterion()
    optimizer = optimizer(model.parameters())
    for e in range(n_epoches):
        running_loss = 0
        for i, (images, labels) in enumerate(trainloader):
            print(f"Epoch {e} Minibatch {i}")
            perturbs = attack.fgsm_array(model, criterion, images, labels)
            adver_images = images + 0.2 * perturbs
            X = torch.cat([images, adver_images], 0)
            y = torch.cat([labels, labels], 0)

            optimizer.zero_grad()

            output = F.log_softmax(model(X), dim=1)
            loss = criterion(output, y)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()
        else:
            print(f"\tTraining loss: {running_loss/len(trainloader)}")
    log.info(f"Training ended: {get_time()}")
    return model