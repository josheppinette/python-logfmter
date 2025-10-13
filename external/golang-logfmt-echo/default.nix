{
  pkgs ? import <nixpkgs> { },
}:

with pkgs;
buildGoModule {
  pname = "golang-logfmt-echo";
  version = "0.0.0";
  src = ./.;
  vendorHash = "0sjjj9z1dhilhpc8pq4154czrb79z9cm044jvn75kxcjv6v5l2m5";
}
