# %%
import matplotlib.pyplot as plt
import numpy as np
import numpy.linalg as la
import seaborn as sns
import torch
from torch import nn

from clustre.attacking import fgsm_perturbs, maxloss_perturbs, pgd_perturbs
from clustre.helpers.datasets import mnist_trainloader
from clustre.models import mnist_cnn, mnist_resnet18
from clustre.models.state_dicts import mnist_cnn_state, mnist_resnet18_state

sns.set()


# %%
mnist_cnn.load_state_dict(mnist_cnn_state)
mnist_resnet18.load_state_dict(mnist_resnet18_state)

mnist_cnn.to("cuda")
mnist_resnet18.to("cuda")

# %%
criterion = nn.CrossEntropyLoss()

# %%
cnn_fgsm = []
for X, y in iter(mnist_trainloader):
    X = X.to("cuda")
    y = y.to("cuda")
    p = fgsm_perturbs(mnist_cnn, criterion, X, y)
    cnn_fgsm.append(p)

# %%
cnn_pgd = []
for X, y in iter(mnist_trainloader):
    X = X.to("cuda")
    y = y.to("cuda")
    p = pgd_perturbs(mnist_cnn, criterion, X, y)
    cnn_pgd.append(p)

# %%
cnn_maxloss = []
for X, y in iter(mnist_trainloader):
    X = X.to("cuda")
    y = y.to("cuda")
    p = maxloss_perturbs(mnist_cnn, criterion, X, y)
    cnn_maxloss.append(p)

# %%
resnet18_fgsm = []
for X, y in iter(mnist_trainloader):
    X = X.to("cuda")
    y = y.to("cuda")
    p = fgsm_perturbs(mnist_resnet18, criterion, X, y)
    resnet18_fgsm.append(p)

# %%
resnet18_pgd = []
for X, y in iter(mnist_trainloader):
    X = X.to("cuda")
    y = y.to("cuda")
    p = pgd_perturbs(mnist_resnet18, criterion, X, y)
    resnet18_pgd.append(p)

# %%
resnet18_maxloss = []
for X, y in iter(mnist_trainloader):
    X = X.to("cuda")
    y = y.to("cuda")
    p = maxloss_perturbs(mnist_resnet18, criterion, X, y)
    resnet18_maxloss.append(p)

# %%
cnn_fgsm = torch.cat(cnn_fgsm)
cnn_maxloss = torch.cat(cnn_maxloss)
cnn_pgd = torch.cat(cnn_pgd)

# %%
resnet18_fgsm = torch.cat(resnet18_fgsm)
resnet18_maxloss = torch.cat(resnet18_maxloss)
resnet18_pgd = torch.cat(resnet18_pgd)

# %%
cnn_fgsm = cnn_fgsm.cpu().detach().numpy()
cnn_maxloss = cnn_maxloss.cpu().detach().numpy()
cnn_pgd = cnn_pgd.cpu().detach().numpy()

# %%
resnet18_fgsm = resnet18_fgsm.cpu().detach().numpy()
resnet18_maxloss = resnet18_maxloss.cpu().detach().numpy()
resnet18_pgd = resnet18_pgd.cpu().detach().numpy()

# %%
np.save("playground/perturbs/cnn_fgsm.npy", cnn_fgsm)
np.save("playground/perturbs/cnn_pgd.npy", cnn_pgd)
np.save("playground/perturbs/cnn_maxloss.npy", cnn_maxloss)
np.save("playground/perturbs/resnet18_fgsm.npy", resnet18_fgsm)
np.save("playground/perturbs/resnet18_pgd.npy", resnet18_pgd)
np.save("playground/perturbs/resnet18_maxloss.npy", resnet18_maxloss)

# %%
cnn_fgsm = np.load("playground/perturbs/cnn_fgsm.npy")
cnn_pgd = np.load("playground/perturbs/cnn_pgd.npy")
cnn_maxloss = np.load("playground/perturbs/cnn_maxloss.npy")
resnet18_fgsm = np.load("playground/perturbs/resnet18_fgsm.npy")
resnet18_pgd = np.load("playground/perturbs/resnet18_pgd.npy")
resnet18_maxloss = np.load("playground/perturbs/resnet18_maxloss.npy")

# %%
cnn_random_fgsm = []
for i in range(100):
    p = np.load(
        f"playground/random_fgsm_perturbs/random_fgsm_mnist_cnn_{i}.npy"
    )
    cnn_random_fgsm.append(p)

# %%
resnet18_random_fgsm = []
for i in range(100):
    p = np.load(
        f"playground/random_fgsm_perturbs/random_fgsm_mnist_resnet18_{i}.npy"
    )
    resnet18_random_fgsm.append(p)

# %%
perturbs = [
    cnn_fgsm,
    cnn_pgd,
    cnn_maxloss,
    resnet18_fgsm,
    resnet18_pgd,
    resnet18_maxloss,
] + cnn_random_fgsm

label = [
    "cnn_fgsm",
    "cnn_pgd",
    "cnn_maxloss",
    "resnet18_fgsm",
    "resnet18_pgd",
    "resnet18_maxloss",
] + [f"cnn_random_fgsm_{i}" for i in range(100)]

# %%
dists = []
for i in perturbs:
    s = []
    for j in perturbs:
        norm = 0
        for im1, im2 in zip(i, j):
            norm += la.norm(im1.ravel() - im2.ravel(), ord=1)
        s.append(norm)
    dists.append(s)

# %%
dists = np.array(dists)

# %%
fig, ax = plt.subplots(1, 1, figsize=(10, 10))
ax = sns.heatmap(dists[:-50, :-50])
plt.show()

# %%
