#!/bin/sh

if [ $# -ne 1 ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

version=$1

update_version() {
    local file_path=$1
    local version=$2

    sed -i -e "s/__version__ = \"[^\"]*\"/__version__ = \"$version\"/" \
           -e "s/version = \"[^\"]*\"/version = \"$version\"/" \
           -e "s/anipy-api = \"\^[^\"]*\"/anipy-api = \"^$version\"/" "$file_path"
}

update_version "cli/pyproject.toml" "$version"
update_version "api/pyproject.toml" "$version"
update_version "cli/src/anipy_cli/__init__.py" "$version"
update_version "api/src/anipy_api/__init__.py" "$version"
