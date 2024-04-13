import random
import numpy as np
from model.model import LocalWLNet, WLNet, FWLNet, LocalFWLNet
from model import train
# from datasets import load_dataset, dataset
from operators.datasets import load_dataset, dataset
import torch
from torch.optim import Adam
from ogb.linkproppred import Evaluator
import yaml
import os

import warnings
warnings.filterwarnings("ignore")


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

def evaluate_hits(pos_pred, neg_pred, K):
    results = {}
    evaluator = Evaluator(name='ogbl-collab')
    evaluator.K = K
    hits = evaluator.eval({
        'y_pred_pos': pos_pred,
        'y_pred_neg': neg_pred,
    })['hits@{}'.format(K)]

    results['Hits@{}'.format(K)] = hits


    return results

def testparam(device="cpu", dsname="Celegans"):  # mod_params=(32, 2, 1, 0.0), lr=3e-4
    device = torch.device(device)
    bg = load_dataset(dsname, args.pattern)
    bg.to(device)
    bg.preprocess()
    bg.setPosDegreeFeature()
    max_degree = torch.max(bg.x[2])

    trn_ds = dataset(*bg.split(0))
    val_ds = dataset(*bg.split(1))
    tst_ds = dataset(*bg.split(2))
    if trn_ds.na != None:
        print("use node feature")
        trn_ds.na = trn_ds.na.to(device)
        val_ds.na = val_ds.na.to(device)
        tst_ds.na = tst_ds.na.to(device)
        use_node_attr = True
    else:
        use_node_attr = False


    def valparam(**kwargs):
        lr = kwargs.pop('lr')
        epoch = kwargs.pop('epoch')
        if args.pattern == '2wl':
            mod = WLNet(max_degree, use_node_attr, trn_ds.na, **kwargs).to(device)
        elif args.pattern == '2wl_l':
            mod = LocalWLNet(max_degree, use_node_attr, trn_ds.na, **kwargs).to(device)
        elif args.pattern == '2fwl':
            mod = FWLNet(max_degree, use_node_attr, trn_ds.na, **kwargs).to(device)
        elif args.pattern == '2fwl_l':
            mod = LocalFWLNet(max_degree, use_node_attr, trn_ds.na, **kwargs).to(device)
        opt = Adam(mod.parameters(), lr=lr)
        return train.train_routine(args.dataset, mod, opt, trn_ds, val_ds, tst_ds, epoch, verbose=True)

    file_path = os.path.join("config", args.pattern, "{}.yaml".format(args.dataset))
    with open(file_path) as f:
        params = yaml.safe_load(f)

    valparam(**(params))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--pattern', type=str, default="2wl_l")
    parser.add_argument('--raw_data', type=str, default="fb-pages-food")
    parser.add_argument('--device', type=int, default=-1)
    parser.add_argument('--path', type=str, default="opt/")
    parser.add_argument('--test', action="store_true")
    parser.add_argument('--check', action="store_true")
    parser.add_argument('--seed', type=int, default=0)
    args = parser.parse_args()
    if args.device < 0:
        args.device = "cpu"
    else:
        args.device = "cuda:" + str(args.device)
    print(args.device)
    for i in range(10):
        set_seed(i + args.seed)
        testparam(args.device, args.dataset)