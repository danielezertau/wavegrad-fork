import tensorflow_hub as hub
import numpy as np
import soundfile as sf
from scipy import linalg
import librosa


def _stable_trace_sqrt_product(sigma_test, sigma_train, eps=1e-7):
    sqrt_product, _ = linalg.sqrtm(sigma_test.dot(sigma_train), disp=False)
    if not np.isfinite(sqrt_product).all():
        offset = np.eye(sigma_test.shape[0]) * eps
        sqrt_product = linalg.sqrtm((sigma_test + offset).dot(sigma_train + offset))
    if not np.allclose(np.diagonal(sqrt_product).imag, 0, atol=1e-3):
        raise ValueError('sqrt_product contains large complex numbers.')
    sqrt_product = sqrt_product.real
    return np.trace(sqrt_product)


def get_embeddings(files, model, factor=False, rms=False, prefix=False):
    embedding_lst = []
    for f in files:
        print('file', f)
        # waveform = np.zeros(3 * 16000, dtype=np.float32)
        try:
            audio, sr = sf.read(f, dtype='int16')
        except:
            audio, sr = librosa.load(f, sr=16000)
            audio = (32768. * audio).astype(np.int16)
        if len(audio.shape) == 2:
            audio = audio.astype(float).mean(axis=1)
        else:
            audio = audio.astype(float)
        if prefix:
            audio = audio[: 16000 * prefix]
        waveform = audio
        waveform = waveform / 32768.

        if factor:
            waveform = np.clip(waveform * factor, -1, 1)

        # Run the model, check the output.
        embedding = model(waveform)
        embedding.shape.assert_is_compatible_with([None, 128])
        embedding_lst.append(embedding.numpy())
    return np.concatenate(embedding_lst, axis=0)


def frechet(mu1, sig1, mu2, sig2):
    diff = mu1 - mu2
    frob = np.dot(diff, diff)
    tr_sqrt = _stable_trace_sqrt_product(sig1, sig2)
    return frob + np.trace(sig1) + np.trace(sig2) - 2 * tr_sqrt


if __name__ == '__main__':
    # Load the model.
    model = hub.load('https://tfhub.dev/google/vggish/1')
    print('loaded model')

    eval_files = [
        "./recon128/output-The.wav"]
    # "./recon128/output-Pink.wav"]
    # "./recon128/output-David.wav"]
    # "./recon128/output-Children's.wav"]
    # "./recon128/output-Beethoven.wav"]
    # "./recon128/output-Queen.wav"]
    # "./recon128/output-Come.wav"]
    # "./recon128/output-FranzSchubert-SonataInAMinorD.784-02-Andante.wav"]
    # "./recon128/output-Here.wav"]
    # "./recon128/output-Bach.wav"]# model prediction

    bg_files = [
        "./IdeaProjects/wavegrad-fake-fork/music-inf/The Well Tempered Clavier, Book I, BWV 846-869 - Fugue No.2 in C minor, BWV 847 Short.flac"]
    # "./IdeaProjects/wavegrad-fake-fork/music-inf/Pink Floyd - Money - Pink Floyd HD (Studio Version) Short.flac"]
    # "./IdeaProjects/wavegrad-fake-fork/music-inf/David Bowie - Changes Short.flac"]
    # "./IdeaProjects/wavegrad-fake-fork/music-inf/Children's Corner, L. 113 - I. Doctor Gradus ad Parnassum Short.flac"]
    # "./IdeaProjects/wavegrad-fake-fork/music-inf/Beethoven - Symphony No. 9 in D minor, Op. 125 - II. Scherzo_ Molto Vivace - Presto Short.flac"]
    # "./IdeaProjects/wavegrad-fake-fork/music-inf/Queen - I Want To Break Free Short.flac"]
    # "./IdeaProjects/wavegrad-fake-fork/music-inf/Come Together (Remastered 2009) Short.flac"]
    # "./IdeaProjects/wavegrad-fake-fork/music-inf/FranzSchubert-SonataInAMinorD.784-02-Andante Short.flac"]
    # "./IdeaProjects/wavegrad-fake-fork/music-inf/Here Majesty (Remastered 2009).flac"]
    # "./IdeaProjects/wavegrad-fake-fork/music-inf/Bach - Cello Suite No.5 6-Gigue Short.flac"]  # ground truth or target

    eval_embeddings = get_embeddings(eval_files, model)
    bg_embeddings = get_embeddings(bg_files, model)

    mu_e = eval_embeddings.mean(axis=0)
    sigma_e = np.cov(eval_embeddings, rowvar=False)

    mu_bg = bg_embeddings.mean(axis=0)
    sigma_bg = np.cov(bg_embeddings, rowvar=False)
    frechet_dist = frechet(mu_e, sigma_e, mu_bg, sigma_bg)
    print('frechet', frechet_dist)
    print('done.')
