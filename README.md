<div align="center">

  # film-central
  <sub>A mov-cli plugin for watching Films and Shows.</sub>

  <img src="https://github.com/mov-cli/mov-cli-vadapav/assets/132799819/6406133d-f840-424b-a1c9-04599fadb0a7">

</div>

> [!CAUTION]
> We are on the lookout for maintainers and if we don't find any soon this project may become unmaintained! Please consider or nominate a friend. Thank you.

## Installation
Here's how to install and add the plugin to mov-cli.

> [!WARNING]
> Before installing this plugin make sure ``mov-cli-films`` is not installed to lower the risks of a conflict.
> ``pip uninstall mov-cli-films``

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