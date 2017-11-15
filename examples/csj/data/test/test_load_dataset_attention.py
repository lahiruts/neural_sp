#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import sys
import unittest

sys.path.append(os.path.abspath('../../../../'))
from examples.csj.data.load_dataset_attention import Dataset
from utils.io.labels.character import Idx2char
from utils.io.labels.word import Idx2word
from utils.measure_time_func import measure_time


class TestLoadDatasetAttention(unittest.TestCase):

    def test(self):

        # data_type
        self.check(label_type='kanji', data_type='train')
        self.check(label_type='kanji', data_type='dev')
        self.check(label_type='kanji', data_type='eval1')
        # self.check(label_type='kanji', data_type='eval2')
        # self.check(label_type='kanji', data_type='eval3')

        # label_type
        self.check(label_type='word_freq1')
        self.check(label_type='word_freq5')
        self.check(label_type='word_freq10')
        self.check(label_type='word_freq15')
        self.check(label_type='kanji_divide')
        self.check(label_type='kana')
        self.check(label_type='kana_divide')

        # sort
        self.check(label_type='kanji', sort_utt=True)
        self.check(label_type='kanji', sort_utt=True,
                   sort_stop_epoch=True)

        # frame stacking
        self.check(label_type='kanji', frame_stacking=True)

        # splicing
        self.check(label_type='kanji', splice=11)

        # multi-GPU
        self.check(label_type='kanji', num_gpus=8)

    @measure_time
    def check(self, label_type, data_type='dev', data_size='subset',
              shuffle=False, sort_utt=True, sort_stop_epoch=None,
              frame_stacking=False, splice=1, num_gpus=1):

        print('========================================')
        print('  label_type: %s' % label_type)
        print('  data_type: %s' % data_type)
        print('  data_size: %s' % data_size)
        print('  shuffle: %s' % str(shuffle))
        print('  sort_utt: %s' % str(sort_utt))
        print('  sort_stop_epoch: %s' % str(sort_stop_epoch))
        print('  frame_stacking: %s' % str(frame_stacking))
        print('  splice: %d' % splice)
        print('  num_gpus: %d' % num_gpus)
        print('========================================')

        if 'kana' in label_type:
            vocab_file_path = '../../metrics/vocab_files/' + label_type + '.txt'
        else:
            vocab_file_path = '../../metrics/vocab_files/' + \
                label_type + '_' + data_size + '.txt'

        num_stack = 3 if frame_stacking else 1
        num_skip = 3 if frame_stacking else 1
        dataset = Dataset(
            data_type=data_type, data_size=data_size,
            label_type=label_type, vocab_file_path=vocab_file_path,
            batch_size=64, max_epoch=2, splice=splice,
            num_stack=num_stack, num_skip=num_skip,
            shuffle=shuffle,
            sort_utt=sort_utt, reverse=True, sort_stop_epoch=sort_stop_epoch,
            num_gpus=num_gpus)

        print('=> Loading mini-batch...')

        idx2char = Idx2char(vocab_file_path)
        idx2word = Idx2word(vocab_file_path)

        for data, is_new_epoch in dataset:
            inputs, labels, inputs_seq_len, labels_seq_len, input_names = data

            if data_type == 'train':
                for i, l in zip(inputs[0], labels[0]):
                    if len(i) < len(l):
                        raise ValueError(
                            'input length must be longer than label length.')

            if num_gpus > 1:
                for inputs_gpu in inputs:
                    print(inputs_gpu.shape)

            if 'eval' in data_type:
                str_true = labels[0][0][0]
            else:
                if 'word' in label_type:
                    str_true = '_'.join(
                        idx2word(labels[0][0][1:labels_seq_len[0][0] - 1]))
                else:
                    str_true = idx2char(
                        labels[0][0][1:labels_seq_len[0][0] - 1])

            print('----- %s (epoch: %.3f) -----' %
                  (input_names[0][0], dataset.epoch_detail))
            print(inputs[0].shape)
            print(labels[0].shape)
            print(str_true)

            if dataset.epoch_detail >= 0.05:
                break


if __name__ == '__main__':
    unittest.main()
