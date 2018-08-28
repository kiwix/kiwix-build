#!/usr/bin/perl

use utf8;
use strict;
use warnings;
use Getopt::Long;

# get the params
my $zim_url;
my $custom_app;
my $keystore;
my $api_key;
my $version = "0";
my $cmd;

# Get console line arguments
GetOptions('zim_url=s' => \$zim_url,
	   'custom_app=s' => \$custom_app,
	   'keystore=s' => \$keystore,
	   'api_key=s' => \$api_key,
	   'version=s' => \$version
	   );

# Print usage() if necessary
if (!$zim_url || !$custom_app || !$keystore || !$api_key) {
    print "usage: ./build_custom_app.pl --keystore=kiwix-android.keystore --api_key=google.json --zim_url=\"https://download.kiwix.org/zim/wikipedia_en_medicine_novid.zim\" --custom_app=wikimed [--version=1]\n";
    exit;
}

# Clean signed ap
$cmd = "rm ./signed_apks/*apk"; `$cmd`;

# Download ZIM file
$cmd = "wget \"$zim_url\" -O content.zim"; `$cmd`;

# Get ZIM file size
$cmd = "stat -c %s content.zim";
my $zim_size = `$cmd` =~ s/\n//gr ;
$ENV{ZIM_SIZE} = $zim_size;

# Compute version code base
$cmd = "date +%y%j";
my $version_code_base = `$cmd` =~ s/\n//gr . $version;

# Compute content version code
my $content_version_code = $version_code_base;
$ENV{CONTENT_VERSION_CODE} = $content_version_code;

# Compute custom app date
$cmd = "date +%Y-%m";
my $date = `$cmd` =~ s/\n//gr;
$ENV{VERSION_NAME} = $date;

# Compile apps
$ENV{VERSION_CODE} = $version_code_base;
$cmd = "kiwix-build kiwix-android-custom --android-arch arm --android-custom-app $custom_app --zim-file-size $zim_size"; system $cmd;

$cmd = "./BUILD_neutral/TOOLCHAINS/android-sdk-r25.2.3/build-tools/27.0.3/apksigner sign -ks \"${keystore}\" --ks-pass env:KIWIX_KEY --out signed_apks/app-${version_code_base}-release-signed.apk BUILD_android/kiwix-android-custom_${custom_app}/app/build/outputs/apk/${custom_app}/release/app-${custom_app}-release-unsigned.apk";
system $cmd;


$ENV{VERSION_CODE} = "1" . $version_code_base;
$cmd = "kiwix-build kiwix-android-custom --android-arch arm64 --android-custom-app $custom_app --zim-file-size $zim_size"; system $cmd;

$cmd = "./BUILD_neutral/TOOLCHAINS/android-sdk-r25.2.3/build-tools/27.0.3/apksigner sign -ks \"${keystore}\" --ks-pass env:KIWIX_KEY --out signed_apks/app-1${version_code_base}-release-signed.apk BUILD_android/kiwix-android-custom_${custom_app}/app/build/outputs/apk/${custom_app}/release/app-${custom_app}-release-unsigned.apk";
system $cmd;


$ENV{VERSION_CODE} = "2" . $version_code_base;
$cmd = "kiwix-build kiwix-android-custom --android-arch x86 --android-custom-app $custom_app --zim-file-size $zim_size"; system $cmd;

$cmd = "./BUILD_neutral/TOOLCHAINS/android-sdk-r25.2.3/build-tools/27.0.3/apksigner sign -ks \"${keystore}\" --ks-pass env:KIWIX_KEY --out signed_apks/app-2${version_code_base}-release-signed.apk BUILD_android/kiwix-android-custom_${custom_app}/app/build/outputs/apk/${custom_app}/release/app-${custom_app}-release-unsigned.apk";
system $cmd;


$ENV{VERSION_CODE} = "3" . $version_code_base;
$cmd = "kiwix-build kiwix-android-custom --android-arch x86_64 --android-custom-app $custom_app --zim-file-size $zim_size"; system $cmd;

$cmd = "./BUILD_neutral/TOOLCHAINS/android-sdk-r25.2.3/build-tools/27.0.3/apksigner sign -ks \"${keystore}\" --ks-pass env:KIWIX_KEY --out signed_apks/app-3${version_code_base}-release-signed.apk BUILD_android/kiwix-android-custom_${custom_app}/app/build/outputs/apk/${custom_app}/release/app-${custom_app}-release-unsigned.apk";
system $cmd;


$ENV{VERSION_CODE} = "4" . $version_code_base;
$cmd = "kiwix-build kiwix-android-custom --android-arch mips --android-custom-app $custom_app --zim-file-size $zim_size"; system $cmd;

$cmd = "./BUILD_neutral/TOOLCHAINS/android-sdk-r25.2.3/build-tools/27.0.3/apksigner sign -ks \"${keystore}\" --ks-pass env:KIWIX_KEY --out signed_apks/app-4${version_code_base}-release-signed.apk BUILD_android/kiwix-android-custom_${custom_app}/app/build/outputs/apk/${custom_app}/release/app-${custom_app}-release-unsigned.apk";
system $cmd;


$ENV{VERSION_CODE} = "5" . $version_code_base;
$cmd = "kiwix-build kiwix-android-custom --android-arch mips64 --android-custom-app $custom_app --zim-file-size $zim_size"; system $cmd;

$cmd = "./BUILD_neutral/TOOLCHAINS/android-sdk-r25.2.3/build-tools/27.0.3/apksigner sign -ks \"${keystore}\" --ks-pass env:KIWIX_KEY --out signed_apks/app-5${version_code_base}-release-signed.apk BUILD_android/kiwix-android-custom_${custom_app}/app/build/outputs/apk/${custom_app}/release/app-${custom_app}-release-unsigned.apk";
system $cmd;

# Upload

$cmd = "./build_custom_app.py --step publish --custom-app ${custom_app} --google-api-key ${api_key} --zim-path content.zim --apks-dir signed_apks --content-version-code ${content_version_code}";
system $cmd;

exit;
