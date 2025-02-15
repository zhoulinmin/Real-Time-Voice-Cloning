from synthesizer.hparams import hparams
from synthesizer.synthesizer import Synthesizer
from synthesizer import audio
from pathlib import Path
from typing import Union, List
import tensorflow as tf
import numpy as np
import librosa
import soundfile as sf

_model = None   # type: Synthesizer
sample_rate = hparams.sample_rate

# TODO: allow for custom hparams throughout this module?

def load_model(checkpoints_dir: Path):
    global _model
    
    tf.reset_default_graph()
    _model = Synthesizer()
    checkpoint_fpath = tf.train.get_checkpoint_state(checkpoints_dir).model_checkpoint_path
    _model.load(checkpoint_fpath, hparams)
    
    model_name = checkpoints_dir.parent.name.replace("logs-", "")
    step = int(checkpoint_fpath[checkpoint_fpath.rfind('-') + 1:])
    print("Loaded synthesizer \"%s\" trained to step %d" % (model_name, step))

def is_loaded():
    return _model is not None

def synthesize_spectrograms(texts: List[str], embeddings: np.ndarray, return_alignments=False):
    """
    Synthesizes mel spectrograms from texts and speaker embeddings.
    
    :param texts: a list of N text prompts to be synthesized
    :param embeddings: a numpy array of (N, 256) speaker embeddings
    :param return_alignments: if True, a matrix representing the alignments between the characters
    and each decoder output step will be returned for each spectrogram
    :return: a list of N melspectrograms as numpy arrays of shape (80, M), and possibly the 
    alignments.
    """
    if not is_loaded():
        raise Exception("Load a model first")
    
    linear_specs, specs, alignments = _model.my_synthesize(embeddings, texts)
    
    if return_alignments:
        return linear_specs, alignments
    else:
        return linear_specs

def load_preprocess_wav(fpath):
    #wav = librosa.load(fpath, hparams.sample_rate)[0]
    wav = sf.read(fpath)[0]
    if hparams.rescale:
        wav = wav / np.abs(wav).max() * hparams.rescaling_max
    return wav

def make_spectrogram(fpath_or_wav: Union[str, Path, np.ndarray]):
    if isinstance(fpath_or_wav, str) or isinstance(fpath_or_wav, Path):
        wav = load_preprocess_wav(fpath_or_wav)
    else: 
        wav = fpath_or_wav
    
    mel_spectrogram = audio.melspectrogram(wav, hparams).astype(np.float32)
    return mel_spectrogram

def griffin_lim(mel):
    return audio.inv_linear_spectrogram(mel, hparams)


