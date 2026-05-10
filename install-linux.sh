#!/bin/bash

if ! [[ -d $HOME/.local/share/anipy-cli-venv-install ]]; then
  echo creating a python virtual environment
  mkdir $HOME/.local/share/anipy-cli-venv-install
  python -m venv $HOME/.local/share/anipy-cli-venv-install/venv
else
  echo "environment already found"
fi

if ! [[ -f $HOME/.local/share/anipy-cli-venv-install/venv/bin/anipy-cli ]]; then
  echo installing anipy-cli-venv-install
  source $HOME/.local/share/anipy-cli-venv-install/venv/bin/activate
  pip install --upgrade pip
  pip install anipy-cli
  deactivate
else
  echo "anipy-cli already installed"
fi

if ! [[ -f $HOME/.local/bin/anipy-cli ]]; then
  echo creating symlink
  ln -s $HOME/.local/share/anipy-cli-venv-install/venv/bin/anipy-cli $HOME/.local/bin/anipy-cli
else
  echo "symlink already created"
fi

if ! [[ -f $HOME/.local/bin/anipy-cli-update ]]; then
  echo "creating update script"
  echo "#!/bin/bash
  source \$HOME/.local/share/anipy-cli-venv-install/venv/bin/activate
  pip install --upgrade pip
  pip install --upgrade anipy-cli
  deactivate
  rm \$HOME/.local/bin/anipy-cli 
  ln -s \$HOME/.local/share/anipy-cli-venv-install/venv/bin/anipy-cli \$HOME/.local/bin/anipy-cli
   " | sed -e 's/^ *//g' >$HOME/.local/bin/anipy-cli-update
  chmod +x $HOME/.local/bin/anipy-cli-update
else
  echo "update script already created"
fi

if ! [[ -f $HOME/.local/bin/anipy-cli-uninstall ]]; then
  echo "creating uninstall script"
  echo "#!/bin/bash
  rm -r \$HOME/.local/share/anipy-cli-venv-install 
  rm \$HOME/.local/bin/anipy-cli
  rm \$HOME/.local/bin/anipy-cli-update
  rm \$HOME/.local/bin/anipy-cli-uninstall
  " | sed -e 's/^ *//g' >$HOME/.local/bin/anipy-cli-uninstall
  chmod +x $HOME/.local/bin/anipy-cli-uninstall
else
  echo "uninstall script already created"
fi
