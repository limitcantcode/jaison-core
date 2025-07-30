[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/limitcantcode-jaison-core-badge.png)](https://mseep.ai/app/limitcantcode-jaison-core)

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

- Realtime promptable AI personality with text and speech input
- Support for MCP
- REST API and websocket server for building applications on top of this server
- Options to run fully local

## Official Applications

- [Discord bot integration](https://github.com/limitcantcode/app-jaison-discord-lcc)
- [VTube Studio with emotions](https://github.com/limitcantcode/app-jaison-vts-hotkeys-lcc)
- [Twitch Chat and Events content provider](https://github.com/limitcantcode/app-jaison-twitch-lcc)

Feel free to build and share your own! See the [Developer Guide](#developer-guide) for more info.

## Install From Scratch

> **Note**
> To simplify setup across platforms, setup now uses [conda](https://docs.conda.io/projects/conda/en/stable/user-guide/install/index.html). Conda is not necessary to run this project.

### Setup and install dependencies

Create and enter a virtual environment with Python ^3.10 and pip 24.0.

For example, using conda:
```bash
conda create -n jaison-core python=3.10 pip=24.0 -y
conda activate jaison-core
```

<hr />

Install dependencies.

```bash
# Inside project root where this README is located
pip install -r requirements.txt
pip install --no-deps -r requirements.no_deps.txt
python -m spacy download en_core_web_sm
python install.py
python -m unidic download
```


> Dealing with duplicate `libiomp5md.dll`.
> 
> It might not be necessary, but in case you encounter this error when running:
> 
> 1. Go to environment directory (where conda stores installed packages)
> 2. Search for `libiomp5md.dll`
> 3. Delete the version under package `torch`

> If on Windows, please enable [Developer Mode](https://learn.microsoft.com/en-us/windows/apps/get-started/enable-your-device-for-development)

<hr />

Install [PyTorch 2.7.1](https://pytorch.org/get-started/previous-versions/) with the right integration. Example below for computers with RTX graphics card.
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
```

> For NVidia cards, ensure you have the latest drivers and [CUDA toolkit](https://developer.nvidia.com/cuda-toolkit)

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

Configuration

**FOR A FREE, 3RD PARTY T2T INTEGRATION**: Use `openai` type but configure for use with [Groq](https://console.groq.com/home).

Add keys and other sensitive information for services you intend to use in `.env` (make a new file and copy the contents of [`.env-template`](.env-template)).

For immediate setup using the example configuration, just provide the OpenAI API key.

Overall configuration can be done in `configs/` and an example with all configurable options is located in `configs/example.yaml`. See [Development guide](DEVELOPER.md) for details on configuration.


## How To Use

While using the virtual environment with the installation.

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
