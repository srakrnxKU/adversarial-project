import os
import time

import numpy as np

import torch
import torch.nn.functional as F
from torch import nn, optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from torchvision.models import resnet18


def get_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


mnist_transform = transforms.Compose(
    [transforms.ToTensor(), transforms.Normalize((0.5,), (0.5,)),]
)

cifar10_transform = transforms.Compose(
    [transforms.ToTensor(), transforms.Normalize((0.5,), (0.5,))]
)

mnist_trainset = datasets.MNIST(
    root="datasets/mnist", train=True, download=True, transform=mnist_transform
)
mnist_testset = datasets.MNIST(
    root="datasets/mnist",
    train=False,
    download=True,
    transform=mnist_transform,
)

cifar10_trainset = datasets.CIFAR10(
    root="datasets/cifar10",
    train=True,
    download=True,
    transform=cifar10_transform,
)
cifar10_testset = datasets.CIFAR10(
    root="datasets/cifar10",
    train=False,
    download=True,
    transform=cifar10_transform,
)

mnist_trainloader = DataLoader(mnist_trainset, batch_size=128, shuffle=False)
mnist_trainloader_droplast = DataLoader(
    mnist_trainset, batch_size=128, shuffle=False, drop_last=True
)
mnist_testloader = DataLoader(mnist_testset, batch_size=32, shuffle=False)

cifar10_trainloader = DataLoader(
    cifar10_trainset, batch_size=128, shuffle=False
)
cifar10_trainloader_droplast = DataLoader(
    cifar10_trainset, batch_size=128, shuffle=False, drop_last=True
)
cifar10_testloader = DataLoader(cifar10_testset, batch_size=32, shuffle=False)
