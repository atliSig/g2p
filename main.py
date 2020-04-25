"""Sequitur G2P functions"""
# -*- coding: utf-8 -*-
#
# Copyright 2020 Atli Thor Sigurgeirsson <atlithors@ru.is>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import math
import os
import re
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from tqdm import tqdm

from g2p import SequiturTool, Translator, loadG2PSample

from conf import ICE_ALPHABET, SEQUITUR_MDL_PATH, IPA_MAP_PATH, VARIANTS_MASS, VARIANTS_NUMBER

SUB_PATTERN = re.compile(r'[^{}]'.format(ICE_ALPHABET))

TRANSLATOR = None
TRANSLATOR_OPTIONS = None

ipa_map = {}
with open(IPA_MAP_PATH) as f:
    for line in f:
        old, new = line.strip().split('\t')
        ipa_map[old] = new

class Options(dict):
    """Options class for sequitur.Translator"""
    def __init__(self, modelFile=SEQUITUR_MDL_PATH, encoding="UTF-8",
                 variants_number=VARIANTS_NUMBER, variants_mass=VARIANTS_MASS):
        super(Options, self).__init__(
            modelFile=modelFile, encoding=encoding,
            variants_number=variants_number,
            variants_mass=variants_mass)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            return None

    def __setattr__(self, name, value):
        self[name] = value


def predict(words):
    '''
    Input arguments:
    * words (list): A list of strings
    * translator (g2p.Translator instance)
    * options (Options instance): The options that have been
    passed onto translator

    Yields:
    [{"word": word_1, "results":results_1}, ...]
    where word_1 is the first word in words and results_1 is a
    list of dictionaries where e.g.
    result_1 = [{'posterior':posterior_1, 'pronounciation':pron_1}, ...]
    where pron_1 is a string of phoneme predictions, each phoneme seperated
    by a space.
    '''

    for word in words:
        left = tuple(word)
        output = {
            "word": word,
            "results": []}
        try:
            total_posterior = 0.0
            n_variants = 0
            n_best = TRANSLATOR.nBestInit(left)
            while (
                    total_posterior < TRANSLATOR_OPTIONS.variants_mass and
                    n_variants < TRANSLATOR_OPTIONS.variants_number):
                try:
                    log_like, result = TRANSLATOR.nBestNext(n_best)
                except StopIteration:
                    break
                posterior = math.exp(log_like - n_best.logLikTotal)
                output["results"].append(
                    {"posterior": posterior, "pronunciation": " ".join(
                        result)}
                )
                total_posterior += posterior
                n_variants += 1

        except TRANSLATOR.TranslationFailure:
            pass
        yield output


def get_phones(utt, translator_options=None):
    '''
    Takes a string forming a sentence and returns a list of
    phonetic predictions for each word.

    Input arguments:
    * utt (str): A string of words seperated by a space forming a sentence.
    '''
    global TRANSLATOR
    global TRANSLATOR_OPTIONS
    if translator_options is None:
        TRANSLATOR_OPTIONS = Options(
            modelFile=os.getenv("G2P_MODEL", SEQUITUR_MDL_PATH))
        TRANSLATOR = Translator(SequiturTool.procureModel(
            TRANSLATOR_OPTIONS, loadG2PSample))
    else:
        TRANSLATOR_OPTIONS = translator_options
        TRANSLATOR = Translator(SequiturTool.procureModel(
            TRANSLATOR_OPTIONS, loadG2PSample))

    words = [normalize_word(w) for w in utt.strip().split()]
    predictions = list(predict(words))
    phones = []
    for pred in predictions:
        phones.append(pred['results'][0]['pronunciation'])
    return phones


def normalize_word(word, sub_pattern=SUB_PATTERN):
    '''
    A normalization step used specifically for Sequitur.
    The word given as input is lowercased and any character
    not matched by sub_pattern is replaced with the empty string.

    Input arguments:
    * word (string): The word to be normalized
    * sub_pattern (A compiled regex pattern): A substitution pattern
    '''
    word = word.lower()
    word = re.sub(sub_pattern, '', word)
    return word


def g2p_file(
        src_path: str, out_path: str, n_jobs: int = 16,
        translator_options=None):
    '''
    Do grapheme-to-phoneme predictions on a list of utterances
    in a single file.

    Input arguments:
    * src_path (str): The path to the file containing multiple
    utterances, one per line
    * out_path (str): The target path the the file that stores
    the results.
    * n_jobs (int): The maximum number of processes that can
    be used to execute the given calls.
    * contains_scores (bool): If True, each line in the input file
    is e.g. <sentence>\t<source_id>\t<score> else it is
    <sentence>\t<source_id>
    * translator_options (Options instance): Options passed onto g2p.Translator
    '''
    global TRANSLATOR
    global TRANSLATOR_OPTIONS
    if translator_options is None:
        TRANSLATOR_OPTIONS = Options(
            modelFile=os.getenv("G2P_MODEL", SEQUITUR_MDL_PATH))
        TRANSLATOR = Translator(SequiturTool.procureModel(
            TRANSLATOR_OPTIONS, loadG2PSample))
    else:
        TRANSLATOR_OPTIONS = translator_options
        TRANSLATOR = Translator(SequiturTool.procureModel(
            TRANSLATOR_OPTIONS, loadG2PSample))

    executor = ProcessPoolExecutor(max_workers=n_jobs)
    futures = []
    with open(src_path, 'r') as utt_file:
            for line in utt_file:
                futures.append([line, executor.submit(
                    partial(get_phones, line))])

    with open(out_path, 'w') as out_file:
        results = [
            (future[0], future[1].result()) for future
            in tqdm(futures) if future[1].result() is not None]
        for res in results:
            out_file.write('{}\t~ {} ~\n'.format(
                res[0].strip(), '\t'.join(res[1][:])))