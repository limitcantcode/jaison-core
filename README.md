<h1 align="center">Project J.A.I.son</h1>

<img src="docs/assets/banner.png" alt="Project J.A.I.son" width="1920">

<h4 align="center">Core server for building AI Companion applications.</h4>

<p align="center">
  <img alt="Project JAIson badge" src="https://img.shields.io/badge/Project-JAIson-blue">
  <img alt="Github Release" src="https://img.shields.io/github/v/release/limitcantcode/jaison-core" />
  <img alt="GitHub Contributors" src="https://img.shields.io/github/contributors/limitcantcode/jaison-core" />
  <img alt="Issues" src="https://img.shields.io/github/issues/limitcantcode/jaison-core" />
  <img alt="GitHub pull requests" src="https://img.shields.io/github/issues-pr/limitcantcode/jaison-core" />
</p>

<p align="center" >
  <a href="#about-this-project">About This Project</a> •
  <a href="#key-features">Key Features</a> •
  <a href="#applications">Applications</a> •
  <a href="#install-from-scratch">Install From Scratch</a> •
  <a href="#operations">Operations</a> •
  <a href="#how-to-use">How To Use</a> •
  <a href="#developer-guide">Developer Guide</a> •
  <a href="#Community">Community</a> •
  <a href="#thank-you-to-all-the-contributors">Credits</a> •
  <a href="#license">License</a>
</p>

## About This Project

This project is for a fully customizable AI persona usable for streaming or private companionship. Feel free to download and use how you wish. 

This software uses libraries from the FFmpeg project under the LGPLv2.1

## Key Features

- Configurable AI persona that integrates with applications for general interaction and streaming
- Text and talk with AI persona in real-time
- Support for various services and local models
- Support for custom contexts

## Official Applications

- [Discord bot integration](https://github.com/limitcantcode/app-jaison-discord-lcc)
- [VTube Studio with emotions](https://github.com/limitcantcode/app-jaison-vts-hotkeys-lcc)
- [Twitch Chat and Events content provider](https://github.com/limitcantcode/app-jaison-twitch-lcc)

Feel free to build and share your own! See the [Developer Guide](#developer-guide) for more info.

## Install From Scratch

> **Note**
> To simplify setup across platforms, setup now uses [conda](https://docs.conda.io/projects/conda/en/stable/user-guide/install/index.html). Conda is not necessary to run this project.

### Setup and install dependencies

Create and enter a virtual environment with specific Python and pip version.
```bash
conda create -n jaison-core python=3.12 pip=24.0 -y
conda activate jaison-core
```

<hr />

Install [PyTorch 2.5.1](https://pytorch.org/get-started/previous-versions/) with the right integration. Example below for computers with RTX graphics card.
```bash
conda install pytorch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 pytorch-cuda=12.4 -c pytorch -c nvidia
```

> For NVidia cards, ensure you have the latest drivers and [CUDA toolkit](https://developer.nvidia.com/cuda-toolkit)

<hr />

Install remaining dependencies.
```bash
pip install .
python -m spacy download en_core_web_sm
```

<hr />

Install FFmpeg
#### For Ubuntu/Debian users
```bash
sudo apt install ffmpeg
```
#### For MacOS users
```bash
brew install ffmpeg
```
#### For Windows users
Download executables and place them in the root folder:
- [Download latest `ffmpeg-git-essentials.7z`](https://www.gyan.dev/ffmpeg/builds/)
- Extract and copy all contents from `bin/` to root of this project.

<hr />

Add keys and other sensitive information for services you intend to use in `.env` (make a new file and copy the contents of [`.env-template`](.env-template))


<hr />

Dealing with duplicate `libiomp5md.dll`.
1. Go to environment directory (where conda stores installed packages)
2. Search for `libiomp5md.dll`
3. Delete the version under package `torch`

## How To Use

```bash
python ./src/main.py --help
```

Example usage: `python ./src/main.py --config=example`

## Developer Guide

See the specification for building applciations for Project J.A.I.son, creating custom integrations, and configuration tips below:

- [REST API spec](api.yaml)
- [Development guide](DEVELOPER.md)
- [Contributing guidelines](CONTRIBUTING.md)

## Community

Join the community!

- [Discord](https://discord.gg/Z8yyEzHsYM)
- [Youtube](https://www.youtube.com/@LimitCantCode)
- [Twitch](https://www.twitch.tv/atmylimit_)

## Thank you to all the contributors!

[Become a contributor as well](CONTRIBUTING.md)

<a href="https://github.com/limitcantcode/jaison-core/graphs/contributors" target="_blank">
  <img src="https://contrib.rocks/image?repo=limitcantcode/jaison-core" />
</a>

## License

[MIT](LICENSE)
