"""Download runtime NLP assets (NLTK corpora and UniDic). Run after deps are installed."""

import subprocess
import sys

import nltk


def main() -> None:
    print("Downloading NLTK resource averaged_perceptron_tagger_eng...")
    nltk.download("averaged_perceptron_tagger_eng", quiet=False)

    print("Downloading UniDic (python -m unidic download)...")
    subprocess.run([sys.executable, "-m", "unidic", "download"], check=True)

    print("install.py finished.")


if __name__ == "__main__":
    main()
