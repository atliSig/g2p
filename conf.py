"""Wrapper for global parameters"""
# -*- coding: utf-8 -*-

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

import os
from pathlib import Path

# Parameters
VARIANTS_NUMBER = 4
VARIANTS_MASS = 0.9


# Paths
ROOT_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
DATA_DIR = ROOT_DIR / 'data'
SEQUITUR_MDL_PATH = DATA_DIR / 'ipd_clean_slt2018.mdl'
IPA_MAP_PATH = DATA_DIR / 'aipa-map.tsv'

# Graphemes
ICE_ALPHABET = 'aábdðeéfghiíjklmnoóprstuúvxyýþæö'