[![CircleCI](https://circleci.com/gh/digitalfabrik/integreat-cms.svg?style=shield)](https://circleci.com/gh/digitalfabrik/integreat-cms)
[![Pylint](https://img.shields.io/badge/pylint-10.00-brightgreen)](https://www.pylint.org/)
![Coverage](https://img.shields.io/codeclimate/coverage/digitalfabrik/integreat-cms)
[![PyPi](https://img.shields.io/pypi/v/integreat-cms.svg)](https://pypi.org/project/integreat-cms/)
[![Release Notes](https://img.shields.io/badge/%F0%9F%93%9C-release%20notes-blue)](https://digitalfabrik.github.io/integreat-cms/release-notes.html)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# Integreat Django CMS

[![Logo](.github/logo.png) Integreat - The mobile guide for newcomers.](https://integreat-app.de/en/) Multilingual. Offline. Open Source.

This content management system helps local integration experts to provide multilingual information for newcomers.

## Development Setup

This section provides a brief overview of setting up the development environment. We support various environments: you can set up everything locally using your preferred package manager, use it as a devcontainer, or utilize the nix-flake ([coming soon](https://github.com/digitalfabrik/integreat-cms/pull/2730)). Please clone the repository with the following snippet before starting to
setup your development environment.

````
git clone git@github.com:digitalfabrik/integreat-cms.git
cd integreat-cms
````

### Local Setup

To configure your development environment on your system, please follow these steps carefully.

1. Ensure that the following packages are installed alongside your preferred IDE:
   - `npm` version 7 or later
   - `nodejs` version 18 or later
   - `python3` version 3.11 or later
   - `python3-pip` (Debian-based distributions) / `python-pip` (Arch-based distributions)
   - `python3-venv` (only on Debian-based distributions)
   - `gettext` for translation features
   - Either `postgresql` **or** `docker` to run a local database server
2. Execute `tools/install.sh` to download all dependencies.
3. Execute `tools/migrate.sh` to apply all database schema migrations.
4. Optionally, run `tools/loadtestdata.sh` to apply a predefined set of test data.

### Devcontainer

To configure your development container, please follow these steps carefully.

1. Make sure you have Docker and VSCode (not VSCodium) installed on your machine.
2. Open the project in VSCode.
3. If you're opening VSCode for the first time, you'll be prompted to install the ["Dev Containers" extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers). Click "Install" to proceed.
4. Open the command palette (Ctrl + Shift + P or Cmd + Shift + P on macOS) and search for "> Remote-Containers: Open Folder in Container".
5. VSCode will open the project in a new container, install all further required tools and load the testdata.

#### Known Limitations

The perfect is the enemy of the good; thus, this section illuminates aspects of our evolving development setup.

##### Sharing git username and email

A known limitation exists where certain versions of Visual Studio Code (VSCode) may not copy the user's `.gitconfig` file correctly into the Devcontainer environment. In such cases, when you attempt to commit changes within the Devcontainer, you may be prompted to enter your Git username and email every time. This can be inconvenient and disrupt the workflow. However, there is a workaround for this issue. You can resolve it by appending the content of your personal `.gitconfig` file, located at `$HOME/.gitconfig`, to the end of the repository-specific `.git/config` file, which in this case would be `integreat-cms/.git/config`. By doing so, you ensure that the necessary Git configuration settings are correctly applied within the Devcontainer environment, allowing for a smoother development experience.

For more information, refer to [this issue](https://github.com/microsoft/vscode-remote-release/issues/1729) in the VSCode Remote Extension repository.

##### Docker permissions

The user must be in the docker group on linux, VSCode does not allow to optionally enter sudo password.

### Run development server

Run the development server using `/tools/run.sh`, then open your browser and go to `http://localhost:8000`. The default login credentials are username: "root" and password: "root1234".

## Documentation

For detailed instructions, tutorials and the source code reference have a look at our great documentation:

<p align="center">:notebook: https://digitalfabrik.github.io/integreat-cms/</p>

Alternatively, you can generate it yourself using the `tools/make_docs.sh` script.


## Project Architecture / Reference

- [Integreat CMS](integreat_cms): The main package of the integreat-cms with the following sub-packages:
	- [API](integreat_cms/api): This app provides wrapper functions around all API routes and classes mapping the cms models to API JSON responses.
	- [CMS](integreat_cms/cms): This app contains all database models, views, forms and templates forming the content management system for backend users.
	- [Core](integreat_cms/core): This is the project’s main app which contains all configuration files.
	- [Firebase API](firebase_api): This app provides wrapper functions around the Firebase API to send push notifications.
	- [GVZ API](integreat_cms/gvz_api): This app provides wrapper functions around our Gemeindeverzeichnis API to automatically import coordinates and region aliases.
	- [Nominatim API](nominatim_api): This app provides wrapper functions around our Nominatim API to automatically import region bounding boxes.
	- [Sitemap](integreat_cms/sitemap): This app dynamically generates a sitemap.xml for the webapp.
	- [SUMM.AI API](integreat_cms/summ_ai_api): This app provides wrapper functions around the SUMM.AI API for automatic translations into Easy German.
	- [XLIFF](integreat_cms/xliff): This app allows (de-)serialization of translations from/to XLIFF (XML Localization Interchange File Format) for standardised exchange with translation agencies.
- [Tests](tests): This app contains all tests to verify integreat-cms works as intended

To better understand the overall intention it might also be helpful to look at the [wiki for municipalities (GER)](https://wiki.integreat-app.de/) that teaches how to use our CMS.


## License

Copyright © 2018 [Tür an Tür - Digitalfabrik gGmbH](https://github.com/digitalfabrik) and [individual contributors](https://github.com/digitalfabrik/integreat-cms/graphs/contributors).
All rights reserved.

This project is licensed under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0), see [LICENSE](./LICENSE) and [NOTICE.md](./NOTICE.md).
