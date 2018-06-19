#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Evaluate the RNNLM (Librispeech corpus)."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from os.path import join, abspath
import sys
import argparse

sys.path.append(abspath('../../../'))
from models.load_model import load
from examples.librispeech.s5.exp.dataset.load_dataset_lm import Dataset
from examples.librispeech.s5.exp.metrics.lm import eval_ppl
from utils.config import load_config
from utils.evaluation.logging import set_logger

parser = argparse.ArgumentParser()
parser.add_argument('--data_save_path', type=str,
                    help='path to saved data')
parser.add_argument('--model_path', type=str,
                    help='path to the model to evaluate')
parser.add_argument('--epoch', type=int, default=-1,
                    help='the epoch to restore')
parser.add_argument('--eval_batch_size', type=int, default=1,
                    help='the size of mini-batch in evaluation')


def main():

    args = parser.parse_args()

    # Load a config file
    config = load_config(join(args.model_path, 'config.yml'), is_eval=True)
    config['data_size'] = str(config['data_size'])

    # Setting for logging
    logger = set_logger(args.model_path)

    ppl_mean = 0
    for i, data_type in enumerate(['dev_clean', 'dev_other', 'test_clean', 'test_other']):
        # Load dataset
        dataset = Dataset(data_save_path=args.data_save_path,
                          data_type=data_type,
                          data_size=config['data_size'],
                          label_type=config['label_type'],
                          batch_size=args.eval_batch_size,
                          shuffle=False, tool=config['tool'],
                          vocab=config['vocab'])

        if i == 0:
            config['num_classes'] = dataset.num_classes

            # Load model
            model = load(model_type=config['model_type'],
                         config=config,
                         backend=config['backend'])

            # NOTE: after load the rnn config are not a continuous chunk of memory
            # this makes them a continuous chunk, and will speed up forward pass
            model.rnn.flatten_parameters()
            # https://github.com/pytorch/examples/blob/master/word_language_model/main.py

            # Restore the saved parameters
            epoch, _, _, _ = model.load_checkpoint(
                save_path=args.model_path, epoch=args.epoch)

            # GPU setting
            model.set_cuda(deterministic=False, benchmark=True)

            logger.info('epoch: %d' % (epoch - 1))

        ppl = eval_ppl(models=[model],
                       dataset=dataset,
                       progressbar=True)
        ppl_mean += ppl
        logger.info('  PPL (%s): %.3f' % (data_type, ppl))

    logger.info('PPL (mean): %.3f' % (ppl_mean / 3))


if __name__ == '__main__':
    main()