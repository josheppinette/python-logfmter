{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-24.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    { nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [
            (final: prev: {
              golang-logfmt-echo = prev.callPackage ./external/golang-logfmt-echo { };
            })
          ];
        };
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            pkgs.python39
            pkgs.python310
            pkgs.python311
            pkgs.python312
            pkgs.python313

            # external
            pkgs.golang-logfmt-echo
          ];
          shellHook = "unset PYTHONPATH";
        };
      }
    );
}
