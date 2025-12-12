{
  description = "Anime from the comfort of your Terminal";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    poetry2nix = {
      url = "github:sdaqo/poetry2nix?ref=update-vendored-pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, poetry2nix }:
  let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
    inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryApplication defaultPoetryOverrides;
    myPythonApp = mkPoetryApplication {
      projectDir = ./cli/.;
      preferWheels = true;
      overrides = defaultPoetryOverrides.extend (
        final: prev: {
          python-mpv = prev.python-mpv.overridePythonAttrs (old: {
            buildInputs = (old.buildInputs or [ ]) ++ [ prev.setuptools ];
          });
          pyee = prev.pyee.overridePythonAttrs (old: {
            postPatch = "";
          });
        }
      );
    };
  in
  {
    packages.${system}.default = myPythonApp;

    apps.${system}.default = {
      type = "app";
      program = "${myPythonApp}/bin/anipy-cli";
    };
  };
}
