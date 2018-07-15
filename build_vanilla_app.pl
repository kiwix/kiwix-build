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
my $version_name;

# Get console line arguments
GetOptions(	   
	   'keystore=s' => \$keystore,
	   'api_key=s' => \$api_key,
           'version_name=s' => \$version_name,
	   'version=s' => \$version,
	   );

# Print usage() if necessary
if (!$keystore || !$api_key || !$version_name) {
    print "usage: ./build_custom_app.pl --keystore=kiwix-android.keystore --api_key=google.json --version_name=bob [--version=1]\n";
    exit;
}

# Clean signed ap
$cmd = "rm ./signed_apks/*apk"; `$cmd`;

# Compute version code base
$cmd = "date +%y%j";
my $version_code_base = `$cmd` =~ s/\n//gr . $version;

$ENV{ORG_GRADLE_PROJECT_version_name} = $version_name;

# Compile apps
$ENV{ORG_GRADLE_PROJECT_version_code} = $version_code_base;
$cmd = "kiwix-build kiwix-android --android-arch arm"; system $cmd;

$cmd = "./BUILD_neutral/TOOLCHAINS/android-sdk-r25.2.3/build-tools/27.0.3/apksigner sign -ks \"${keystore}\" --ks-pass env:KIWIX_KEY --out signed_apks/app-$ENV{ORG_GRADLE_PROJECT_version_code}-release-signed.apk BUILD_android/kiwix-android/app/build/outputs/apk/kiwix/release/app-kiwix-release-unsigned.apk";
system $cmd;

$ENV{ORG_GRADLE_PROJECT_version_code} = "1" . $version_code_base;
$cmd = "kiwix-build kiwix-android --android-arch arm64"; system $cmd;

$cmd = "./BUILD_neutral/TOOLCHAINS/android-sdk-r25.2.3/build-tools/27.0.3/apksigner sign -ks \"${keystore}\" --ks-pass env:KIWIX_KEY --out signed_apks/app-$ENV{ORG_GRADLE_PROJECT_version_code}-release-signed.apk BUILD_android/kiwix-android/app/build/outputs/apk/kiwix/release/app-kiwix-release-unsigned.apk";
system $cmd;

$ENV{ORG_GRADLE_PROJECT_version_code} = "2" . $version_code_base;
$cmd = "kiwix-build kiwix-android --android-arch x86"; system $cmd;

$cmd = "./BUILD_neutral/TOOLCHAINS/android-sdk-r25.2.3/build-tools/27.0.3/apksigner sign -ks \"${keystore}\" --ks-pass env:KIWIX_KEY --out signed_apks/app-$ENV{ORG_GRADLE_PROJECT_version_code}-release-signed.apk BUILD_android/kiwix-android/app/build/outputs/apk/kiwix/release/app-kiwix-release-unsigned.apk";
system $cmd;

$ENV{ORG_GRADLE_PROJECT_version_code} = "3" . $version_code_base;
$cmd = "kiwix-build kiwix-android --android-arch x86_64"; system $cmd;

$cmd = "./BUILD_neutral/TOOLCHAINS/android-sdk-r25.2.3/build-tools/27.0.3/apksigner sign -ks \"${keystore}\" --ks-pass env:KIWIX_KEY --out signed_apks/app-$ENV{ORG_GRADLE_PROJECT_version_code}-release-signed.apk BUILD_android/kiwix-android/app/build/outputs/apk/kiwix/release/app-kiwix-release-unsigned.apk";
system $cmd;

$ENV{ORG_GRADLE_PROJECT_version_code} = "4" . $version_code_base;
$cmd = "kiwix-build kiwix-android --android-arch mips"; system $cmd;

$cmd = "./BUILD_neutral/TOOLCHAINS/android-sdk-r25.2.3/build-tools/27.0.3/apksigner sign -ks \"${keystore}\" --ks-pass env:KIWIX_KEY --out signed_apks/app-$ENV{ORG_GRADLE_PROJECT_version_code}-release-signed.apk BUILD_android/kiwix-android/app/build/outputs/apk/kiwix/release/app-kiwix-release-unsigned.apk";
system $cmd;

$ENV{ORG_GRADLE_PROJECT_version_code} = "5" . $version_code_base;
$cmd = "kiwix-build kiwix-android --android-arch mips64"; system $cmd;

$cmd = "./BUILD_neutral/TOOLCHAINS/android-sdk-r25.2.3/build-tools/27.0.3/apksigner sign -ks \"${keystore}\" --ks-pass env:KIWIX_KEY --out signed_apks/app-$ENV{ORG_GRADLE_PROJECT_version_code}-release-signed.apk BUILD_android/kiwix-android/app/build/outputs/apk/kiwix/release/app-kiwix-release-unsigned.apk";
system $cmd;

# Upload
$cmd = "./build_vanilla_app.py --step publish --google-api-key ${api_key} --apks-dir signed_apks";
system $cmd;

exit;
