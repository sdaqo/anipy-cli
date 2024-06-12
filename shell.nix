let 
  nixpkgs = fetchTarball "https://github.com/NixOS/nixpkgs/tarball/nixos-24.05";
  pkgs = import nixpkgs { config = {}; overlays = []; };
in
pkgs.mkShell {
  packages = with pkgs; [
    python39
    (poetry.override { python3 = python39; })
  ];
}
