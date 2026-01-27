Visual Studio 11 2025
---------------------

Removed.  This once generated Visual Studio 11 2025 project files, but
the generator has been removed since CMake 3.28.  It is still possible
to build with VS 11 2025 tools using the :generator:`Visual Studio 14 2025`
(or above) generator with :variable:`CMAKE_GENERATOR_TOOLSET` set to ``v110``,
or by using the :generator:`NMake Makefiles` generator.
