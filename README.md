<div align="center">

  # film-central
  <sub>A mov-cli plugin for watching Films and Shows.</sub>

  [![Pypi Version](https://img.shields.io/pypi/v/film-central?style=flat)](https://pypi.org/project/film-central)

  <img src="https://github.com/JDALab/film-central/assets/123201787/e8150d96-64bf-437b-a768-4fdd6a45a2a0">

</div>

> [!CAUTION]
> We are on the lookout for maintainers and if we don't find any soon this project may become unmaintained! Please consider or nominate a friend. Thank you.

## ⛑️ Support
| Scraper | Status | Films | TV Series | Supports <br> Android & iOS | Notes |
| ------- | ------ | --- | --- | ---------------------- | :------: |
| `bflix` | 🔵 Experimental | ✅ | ❌ | ❌ | **NEW** scraper! Many new films and good quality. |
| `vadapav` | 🟠 Unstable | ✅ | ✅ | ✅ | **May get captchas**, very good quality (Sometimes 4k and high bitrate). |
| `vidsrcto` | 🪦 **Dead** | ✅ | ✅ | ✅ | Site domain is down. |

## Installation
Here's how to install and add the plugin to mov-cli.

1. Install the pip package.
```sh
pip install film-central
```
2. Then add the plugin to your mov-cli config.
```sh
mov-cli -e
```
```toml
[mov-cli.plugins]
films = "film-central"
```

## Usage
```sh
mov-cli -s films the rookie
```
