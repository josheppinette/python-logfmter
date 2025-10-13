{
  pkgs ? import <nixpkgs> { },
}:

with pkgs;
buildGoModule {
  pname = "golang-logfmt-echo";
  version = "0.0.0";
  src = ./.;
  vendorHash = "sha256-qXw5xRuTGcy9JVIMQLdadAc/V09h/HJxYrVfskA/YzQ=";
}
