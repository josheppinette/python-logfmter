{
  pkgs ? import <nixpkgs> { },
}:

with pkgs;
buildGoModule {
  pname = "golang-logfmt-echo";
  version = "0.0.0";
  src = ./.;
  vendorHash = "sha256-Yr+8wpleQTFxCYCCihhU5cyIuo11/66MaGgin2P924I=";
}
