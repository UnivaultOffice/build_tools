#!/usr/bin/env python

import base
import glob
import os
import platform

def _get_program_files_dirs():
  dirs = []
  pf = os.getenv("ProgramFiles", "")
  pfx = os.getenv("ProgramFiles(x86)", "")
  if pf:
    dirs.append(pf)
  if pfx and pfx not in dirs:
    dirs.append(pfx)
  return dirs

def _find_vs_path_for_version(vs_version):
  if vs_version == "2015":
    for root in _get_program_files_dirs():
      path = os.path.join(root, "Microsoft Visual Studio 14.0", "VC")
      if base.is_dir(path):
        return path
    return ""

  editions = ["Enterprise", "Professional", "Community", "BuildTools"]
  for root in _get_program_files_dirs():
    for edition in editions:
      path = os.path.join(root, "Microsoft Visual Studio", vs_version, edition, "VC", "Auxiliary", "Build")
      if base.is_dir(path):
        return path
  return ""

def _qt_root_from_qmake(qmake_path):
  if not qmake_path:
    return ""
  qmake_dir = os.path.dirname(qmake_path)
  if os.path.basename(qmake_dir).lower() != "bin":
    return ""
  compiler_dir = os.path.dirname(qmake_dir)
  compiler_name = os.path.basename(compiler_dir).lower()
  if ("msvc" in compiler_name) or ("mingw" in compiler_name) or ("winrt" in compiler_name) or ("clang" in compiler_name):
    return os.path.dirname(compiler_dir)
  return compiler_dir

def _find_qmake_paths():
  roots = [
    "C:\\Qt",
    "C:\\Qt5",
    os.path.join(os.getenv("LOCALAPPDATA", ""), "Programs", "Qt"),
    os.path.join(os.getenv("ProgramFiles", ""), "Qt"),
    os.path.join(os.getenv("ProgramFiles(x86)", ""), "Qt"),
  ]
  patterns = []
  for root in roots:
    if not root:
      continue
    patterns.append(os.path.join(root, "*", "*", "bin", "qmake.exe"))
    patterns.append(os.path.join(root, "*", "bin", "qmake.exe"))

  results = []
  for pattern in patterns:
    for path in glob.glob(pattern):
      if os.path.isfile(path):
        results.append(os.path.normpath(path))
  return list(dict.fromkeys(results))

def _pick_preferred_qmake(qmake_paths):
  if not qmake_paths:
    return ""
  prefer = [
    "msvc2022_64", "msvc2022",
    "msvc2019_64", "msvc2019",
    "msvc2017_64", "msvc2017",
    "msvc2015_64", "msvc2015",
    "mingw", "clang", "gcc"
  ]
  lower_map = [(p, p.lower()) for p in qmake_paths]
  for tag in prefer:
    for path, lower_path in lower_map:
      if tag in lower_path:
        return path
  return qmake_paths[0]

def _detect_qt_dir():
  qmake_paths = _find_qmake_paths()
  qmake_path = _pick_preferred_qmake(qmake_paths)
  return _qt_root_from_qmake(qmake_path)

def _qt_has_msvc(qt_dir, tag):
  if not qt_dir:
    return False
  return base.is_dir(os.path.join(qt_dir, tag))

def parse():
  configfile = open(base.get_script_dir() + "/../config", "r")
  configOptions = {}
  for line in configfile:
    name, value = line.partition("=")[::2]
    k = name.strip()
    v = value.strip(" '\"\r\n")
    if ("true" == v.lower()):
      v = "1"
    if ("false" == v.lower()):
      v = "0"
    configOptions[k] = v
    os.environ["OO_" + k.upper().replace("-", "_")] = v

  # export options
  global options
  options = configOptions

  # all platforms
  global platforms
  platforms = ["win_64", "win_32", "win_64_xp", "win_32_xp", "win_arm64", 
               "linux_64", "linux_32", "linux_arm64",
               "mac_64", "mac_arm64",
               "ios", 
               "android_arm64_v8a", "android_armv7", "android_x86", "android_x86_64"]

  # correction
  host_platform = base.host_platform()
  
  # platform
  if check_option("platform", "all"):
    if ("windows" == host_platform):
      options["platform"] += " win_64 win_32"
    elif ("linux" == host_platform):
      options["platform"] += " linux_64 linux_32"
    else:
      options["platform"] += " mac_64"

  if check_option("platform", "native"):
    bits = "32"
    if platform.machine().endswith('64'):
      bits = "64"
    if ("windows" == host_platform):
      options["platform"] += (" win_" + bits)
    elif ("linux" == host_platform):
      options["platform"] += (" linux_" + bits)
    else:
      options["platform"] += (" mac_" + bits)

  if ("mac" == host_platform) and check_option("platform", "mac_arm64") and not base.is_os_arm():
    if not check_option("platform", "mac_64"):
      options["platform"] = "mac_64 " + options["platform"]

  if (False):
    # use qemu on deploy for emulation 
    if ("windows" == host_platform) and check_option("platform", "win_arm64") and not base.is_os_arm():
      if not check_option("platform", "win_64"):
        options["platform"] = "win_64 " + options["platform"]

  if check_option("platform", "xp") and ("windows" == host_platform):
    options["platform"] += " win_64_xp win_32_xp"

  if check_option("platform", "android"):
    options["platform"] += " android_arm64_v8a android_armv7 android_x86 android_x86_64"

  # try detect qt dir on windows
  if ("windows" == host_platform) and ("" == option("qt-dir")):
    qt_dir = _detect_qt_dir()
    if qt_dir:
      options["qt-dir"] = qt_dir

  # check vs-version
  if ("windows" == host_platform) and ("" == option("vs-version")):
    if check_option("platform", "win_64_xp") or check_option("platform", "win_32_xp"):
      options["vs-version"] = "2015"
    elif _qt_has_msvc(option("qt-dir"), "msvc2022_64") or _qt_has_msvc(option("qt-dir"), "msvc2022"):
      options["vs-version"] = "2022"
    elif _qt_has_msvc(option("qt-dir"), "msvc2019_64") or _qt_has_msvc(option("qt-dir"), "msvc2019"):
      options["vs-version"] = "2019"
    elif _find_vs_path_for_version("2022") != "":
      options["vs-version"] = "2022"
    elif _find_vs_path_for_version("2019") != "":
      options["vs-version"] = "2019"
    else:
      options["vs-version"] = "2019"

  if ("windows" == host_platform) and ("2019" == option("vs-version")):
    extend_option("config", "vs2019")
  if ("windows" == host_platform) and ("2022" == option("vs-version")):
    extend_option("config", "vs2022")
      
  # sysroot setup
  if "linux" != host_platform and "sysroot" in options:
    options["sysroot"] = ""

  if "linux" == host_platform and "sysroot" in options:
    if options["sysroot"] == "0":
      options["sysroot"] = ""
    elif options["sysroot"] == "1":
      dst_dir = os.path.abspath(base.get_script_dir(__file__) + '/../tools/linux/sysroot')
      dst_dir_amd64 = dst_dir + "/ubuntu16-amd64-sysroot"
      dst_dir_arm64 = dst_dir + "/ubuntu16-arm64-sysroot"
      if not base.is_dir(dst_dir_amd64) or not base.is_dir(dst_dir_arm64):
        base.cmd_in_dir(dst_dir, "python3", ["./fetch.py", "all"])
      options["sysroot_linux_64"] = dst_dir_amd64
      options["sysroot_linux_arm64"] = dst_dir_arm64
    else:
      # specific sysroot => one platform for build!
      options["sysroot"] = "1"
      options["sysroot_linux_64"] = options["sysroot"]
      options["sysroot_linux_arm64"] = options["sysroot"]

  if is_cef_107():
    extend_option("config", "cef_version_107")
  if is_v8_60():
    extend_option("config", "v8_version_60")

  # check vs-path
  if ("windows" == host_platform) and ("" == option("vs-path")):
    options["vs-path"] = _find_vs_path_for_version(options["vs-version"])

  # check sdkjs-plugins
  if not "sdkjs-plugin" in options:
    options["sdkjs-plugin"] = "default"
  if not "sdkjs-plugin-server" in options:
    options["sdkjs-plugin-server"] = "default"

  if check_option("platform", "ios"):
    if not check_option("config", "no_bundle_xcframeworks"):
      if not check_option("config", "bundle_xcframeworks"):
        extend_option("config", "bundle_xcframeworks")

  if check_option("config", "bundle_xcframeworks"):
    if not check_option("config", "bundle_dylibs"):
      extend_option("config", "bundle_dylibs")

  if ("mac" == host_platform) and check_option("module", "desktop"):
    if not check_option("config", "bundle_dylibs"):
      extend_option("config", "bundle_dylibs")

  if check_option("use-system-qt", "1"):
    base.cmd_in_dir(base.get_script_dir() + "/../tools/linux", "python", ["use_system_qt.py"])
    options["qt-dir"] = base.get_script_dir() + "/../tools/linux/system_qt"

  # disable all warnings (enable if needed with core_enable_all_warnings options)
  if not check_option("config", "core_enable_all_warnings"):
    extend_option("config", "core_disable_all_warnings")

  return

def check_compiler(platform):
  compiler = {}
  compiler["compiler"] = option("compiler")
  compiler["compiler_64"] = compiler["compiler"] + "_64"

  if ("" != compiler["compiler"]):
    if ("ios" == platform):
      compiler["compiler_64"] = compiler["compiler"]
    return compiler

  if (0 == platform.find("win")):
    compiler["compiler"] = "msvc" + options["vs-version"]
    compiler["compiler_64"] = "msvc" + options["vs-version"] + "_64"
    if (0 == platform.find("win_arm")):
      compiler["compiler"] = "msvc" + options["vs-version"] + "_arm"
      compiler["compiler_64"] = "msvc" + options["vs-version"] + "_arm64"
  elif (0 == platform.find("linux")):
    compiler["compiler"] = "gcc"
    compiler["compiler_64"] = "gcc_64"
    if (0 == platform.find("linux_arm")) and not base.is_os_arm():
      compiler["compiler"] = "gcc_arm"
      compiler["compiler_64"] = "gcc_arm64"
  elif (0 == platform.find("mac")):
    compiler["compiler"] = "clang"
    compiler["compiler_64"] = "clang_64"
  elif ("ios" == platform):
    compiler["compiler"] = "ios"
    compiler["compiler_64"] = "ios"
  elif (0 == platform.find("android")):
    compiler["compiler"] = platform
    compiler["compiler_64"] = platform

  if base.host_platform() == "mac":
    if not base.is_dir(options["qt-dir"] + "/" + compiler["compiler_64"]):
      if base.is_dir(options["qt-dir"] + "/macos"):
        compiler["compiler"] = "macos"
        compiler["compiler_64"] = "macos"

  return compiler

def check_option(name, value):
  if not name in options:
    return False
  tmp = " " + options[name] + " "
  if (-1 == tmp.find(" " + value + " ")):
    return False
  return True

def option(name):
  if name in options:
    return options[name]
  return ""

def extend_option(name, value):
  if name in options:
    options[name] = options[name] + " " + value
  else:
    options[name] = value

def set_option(name, value):
  options[name] = value

def branding():
  branding = option("branding-name")
  if ("" == branding):
    branding = "univaultoffice"
  return branding

def is_mobile_platform():
  all_platforms = option("platform")
  if (-1 != all_platforms.find("android")):
    return True
  if (-1 != all_platforms.find("ios")):
    return True
  return False

def get_custom_sysroot_bin(platform):
  use_platform = platform
  if "linux_arm64" == platform and not base.is_os_arm():
    # use cross compiler
    use_platform = "linux_64"

  return option("sysroot_" + use_platform) + "/usr/bin"

def get_custom_sysroot_lib(platform, isNatural=False):
  use_platform = platform
  if "linux_arm64" == platform and not base.is_os_arm() and not isNatural:
    # use cross compiler
    use_platform = "linux_64"

  if ("linux_64" == use_platform):
    return option("sysroot_linux_64") + "/usr/lib/x86_64-linux-gnu"
  if ("linux_arm64" == use_platform):
    return option("sysroot_linux_arm64") + "/usr/lib/aarch64-linux-gnu"
  return ""

def parse_defaults():
  defaults_path = base.get_script_dir() + "/../defaults"
  if ("" != option("branding")):
    defaults_path_branding = base.get_script_dir() + "/../../" + option("branding") + "/build_tools/defaults"
    if base.is_file(defaults_path_branding):
      defaults_path = defaults_path_branding
  defaults_file = open(defaults_path, "r")
  defaults_options = {}
  for line in defaults_file:
    name, value = line.partition("=")[::2]
    k = name.strip()
    v = value.strip(" '\"\r\n")
    if ("true" == v.lower()):
      v = "1"
    if ("false" == v.lower()):
      v = "0"
    defaults_options[k] = v

  for name in defaults_options:
    if name in options:
      options[name] = options[name].replace("default", defaults_options[name])
    else:
      options[name] = defaults_options[name]

  if ("config_addon" in defaults_options):
    extend_option("config", defaults_options["config_addon"])

  return

def is_cef_107():
  if ("linux" == base.host_platform()) and (5004 > base.get_gcc_version()) and not check_option("platform", "android"):
    return True
  return False

def is_v8_60():
  if check_option("platform", "linux_arm64"):
    return False

  if ("linux" == base.host_platform()) and (5004 > base.get_gcc_version()) and not check_option("platform", "android"):
    return True

  if ("windows" == base.host_platform()) and ("2015" == option("vs-version")):
    return True

  #if check_option("config", "use_v8"):
  #  return True

  return False
