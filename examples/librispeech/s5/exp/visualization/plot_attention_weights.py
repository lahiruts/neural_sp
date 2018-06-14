#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Plot attention weights of the attention model (Librispeech corpus)."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from os.path import join, abspath, isdir
import sys
import argparse
import shutil

sys.path.append(abspath('../../../'))
from models.load_model import load
from examples.librispeech.s5.exp.dataset.load_dataset import Dataset
from utils.directory import mkdir_join, mkdir
from utils.visualization.attention import plot_attention_weights
from utils.config import load_config

parser = argparse.ArgumentParser()
parser.add_argument('--data_save_path', type=str,
                    help='path to saved data')
parser.add_argument('--model_path', type=str,
                    help='path to the model to evaluate')
parser.add_argument('--epoch', type=int, default=-1,
                    help='the epoch to restore')
parser.add_argument('--eval_batch_size', type=int, default=1,
                    help='the size of mini-batch in evaluation')
parser.add_argument('--beam_width', type=int, default=1,
                    help='the size of beam')
parser.add_argument('--length_penalty', type=float, default=0,
                    help='length penalty in beam search decoding')
parser.add_argument('--coverage_penalty', type=float, default=0,
                    help='coverage penalty in beam search decoding')

MAX_DECODE_LEN_WORD = 200
MIN_DECODE_LEN_WORD = 1
MAX_DECODE_LEN_CHAR = 600
MIN_DECODE_LEN_CHAR = 1


def main():

    args = parser.parse_args()

    # Load a config file
    config = load_config(join(args.model_path, 'config.yml'), is_eval=True)
    config['data_size'] = str(config['data_size'])

    # Load dataset
    dataset = Dataset(data_save_path=args.data_save_path,
                      input_freq=config['input_freq'],
                      use_delta=config['use_delta'],
                      use_double_delta=config['use_double_delta'],
                      data_type='test_clean',
                      # data_type='test_other',
                      data_size=config['data_size'],
                      label_type=config['label_type'],
                      batch_size=args.eval_batch_size,
                      sort_utt=False, reverse=False, tool=config['tool'])
    config['num_classes'] = dataset.num_classes

    # Load model
    model = load(model_type=config['model_type'],
                 config=config,
                 backend=config['backend'])

    # Restore the saved parameters
    model.load_checkpoint(save_path=args.model_path, epoch=args.epoch)

    # GPU setting
    model.set_cuda(deterministic=False, benchmark=True)

    save_path = mkdir_join(args.model_path, 'att_weights')

    # Clean directory
    if save_path is not None and isdir(save_path):
        shutil.rmtree(save_path)
        mkdir(save_path)

    if dataset.label_type == 'word':
        map_fn = dataset.idx2word
        max_decode_len = MAX_DECODE_LEN_WORD
        min_decode_len = MIN_DECODE_LEN_WORD
    else:
        map_fn = dataset.idx2char
        max_decode_len = MAX_DECODE_LEN_CHAR
        min_decode_len = MIN_DECODE_LEN_CHAR

    for batch, is_new_epoch in dataset:
        # Decode
        best_hyps, aw, perm_idx = model.decode(
            batch['xs'],
            beam_width=args.beam_width,
            max_decode_len=max_decode_len,
            min_decode_len=min_decode_len,
            length_penalty=args.length_penalty,
            coverage_penalty=args.coverage_penalty)

        ys = [batch['ys'][i] for i in perm_idx]

        for b in range(len(batch['xs'])):
            # Reference
            if dataset.is_test:
                str_ref = ys[b]
                # NOTE: transcript is seperated by space('_')
            else:
                str_ref = map_fn(ys[b])

            token_list = map_fn(best_hyps[b], return_list=True)
            speaker, chapter = batch['input_names'][b].split('-')[:2]

            plot_attention_weights(
                aw[b][:len(token_list)],
                label_list=token_list,
                spectrogram=batch['xs'][b][:dataset.input_freq],
                str_ref=str_ref,
                save_path=mkdir_join(save_path, speaker, chapter,
                                     batch['input_names'][b] + '.png'),
                figsize=(20, 4))

        if is_new_epoch:
            break


if __name__ == '__main__':
    main()
