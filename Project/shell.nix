{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  name = "invoice-agent-env";
  buildInputs = [
    pkgs.python3Full
    pkgs.python3Packages.pip
    pkgs.python3Packages.virtualenv
  ];
}
